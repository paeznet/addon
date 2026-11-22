# -*- coding: utf-8 -*-
# -*- Channel Doramasflix -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import base64
import re
import sys
import time
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


from core import jsontools, httptools, servertools, tmdb
from platformcode import logger, config
from channelselector import get_thumb
from core.item import Item
from modules import autoplay
from modules import filtertools
from core.jsontools import json

TAG_CHANNEL_LANGUAGE_DATA = "channel_language_data"

canonical = {
             'channel': 'doramasflix', 
             'host': config.get_setting("current_host", 'doramasflix', default=''), 
             'host_alt': ["https://doramasflix.co/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

# Endpoint de la API (GRAPHQL_ENDPOINTS.http del cliente web de Doramasflix)
GRAPHQL_URL = "https://user-api.seriesapi.co/graphql"
# appConfig.android del cliente web: necesario para getEpisodeLinks/getMovieLinks
APP_ID = "com.asiapp.doramasgo"

list_language = ["Subtitulado", "Latino", "Castellano", "Coreano", "Japonés", "Mandarín", "Tailandés", "Filipino", "Indonesio", "Vietnamita", "Portugués"]
list_quality = ['HD']
list_servers = ['uqload', 'voe', 'streamtape', 'doodstream', 'okru', 'streamlare', 'wolfstream', 'mega', 'streamwish', 'filemoon', 'mixdrop']
tmdb_thumb_path = 'https://image.tmdb.org/t/p/original{}'
items_per_page = 10

# La API devuelve los idiomas con códigos numéricos (code_flix) y los nombres sin
# acentos / abreviados. Se normalizan a los nombres usados por el canal para que
# los filtros de idioma de Alfa sigan funcionando.
LANGUAGE_ALIASES = {"Japones": "Japonés",
                    "Tailandes": "Tailandés",
                    "Indones": "Indonesio",
                    "Portugues": "Portugués",
                    "Ingles": "Inglés"
                   }


def read_api(query):
    logger.info()

    post = json.dumps(query)

    headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
              }

    response = httptools.downloadpage(GRAPHQL_URL, headers=headers, post=post, referer=host,
                                      ignore_response_code=True, hide_infobox=True)
    if not response or response.code != 200:
        logger.error("GraphQL: error {} en la petición: {}".format(getattr(response, 'code', ''),
                                                                   str(getattr(response, 'data', ''))[:500]))
        return False

    try:
        data_json = json.loads(response.data)
    except Exception as e:
        logger.error("GraphQL: respuesta no válida: {}".format(str(e)))
        return False

    if data_json.get('errors'):
        logger.error("GraphQL: {}".format(data_json['errors']))

    return data_json


def get_thumb_path(path):
    """Devuelve la URL completa del poster/backdrop devuelto por la API."""

    if not path:
        return ''

    if path.startswith('http'):
        return path

    return tmdb_thumb_path.format(path)


def get_year(date):
    """Extrae el año (int, como tmdb) de las fechas de la API: 'YYYY-MM-DD', timestamps en ms o 'DD-MM-YYYY'."""

    if not date:
        return ''

    date = str(date)

    if date.isdigit():
        try:
            stamp = int(date)
            if stamp > 9999999999:  # viene en milisegundos
                stamp //= 1000
            return int(time.gmtime(stamp).tm_year)
        except Exception:
            return ''

    match = re.search(r'(?<!\d)(\d{4})(?!\d)', date)

    return int(match.group(1)) if match else ''


def get_aired(date):
    """Devuelve la fecha en formato DD/MM/YYYY (igual que tmdb) a partir de las fechas de la API."""

    if not date:
        return ''

    date = str(date)

    if date.isdigit():
        try:
            stamp = int(date)
            if stamp > 9999999999:  # viene en milisegundos
                stamp //= 1000
            return time.strftime('%d/%m/%Y', time.gmtime(stamp))
        except Exception:
            return ''

    # 'YYYY-MM-DD'
    if re.match(r'^\d{4}-\d{2}-\d{2}', date):
        if date[0:4] == '0000':
            return ''
        return "{}/{}/{}".format(date[8:10], date[5:7], date[0:4])

    # 'DD-MM-YYYY'
    if re.match(r'^\d{2}-\d{2}-\d{4}$', date):
        if date[6:10] == '0000':
            return ''
        return date.replace('-', '/')

    return ''


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Nuevos Episodios",
                         action="new_episodes",
                         thumbnail=get_thumb('new_episodes', auto=True),
                         url=host))

    itemlist.append(Item(channel=item.channel, title="Doramas",
                         action="list_all",
                         thumbnail=get_thumb('tvshows', auto=True),
                         url=host, c_type='doramas'))

    itemlist.append(Item(channel=item.channel, title="Películas",
                         action="list_all",
                         thumbnail=get_thumb('movies', auto=True),
                         url=host, c_type='peliculas'))
                         
    itemlist.append(Item(channel=item.channel, title="TvShows",
                         action="list_all",
                         thumbnail=get_thumb('tvshows', auto=True),
                         url=host, c_type='TvShows'))

    itemlist.append(Item(channel=item.channel, title="Buscar",
                         action="search",
                         url=host,
                         thumbnail=get_thumb('search', auto=True),
                         c_type='search'))
                         
    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    page = 1
    if item.page:
        page = item.page

    if item.c_type in ['doramas', 'TvShows']:
        addfilter = {}
        addfilter["isTVShow"] = False if item.c_type == 'doramas' else True

        query = {
                "operationName": "PaginationDorama",
                "variables": {"page": page, "limit": items_per_page, "filter": addfilter},
                "query": "query PaginationDorama($sort: SortDorama, $limit: Int, $filter: FilterDoramasInput, $page: Int) {\n"
                        +"  paginationDorama(sort: $sort, limit: $limit, filter: $filter, page: $page) {\n"
                        +"    count\n"
                        +"    pageInfo {\n"
                        +"      hasNextPage\n"
                        +"      currentPage\n"
                        +"      pageCount\n"
                        +"    }\n"
                        +"    items {\n"
                        +"      _id\n"
                        +"      name\n"
                        +"      name_es\n"
                        +"      slug\n"
                        +"      languages\n"
                        +"      isTVShow\n"
                        +"      first_air_date\n"
                        +"      poster_path\n"
                        +"      poster\n"
                        +"      backdrop_path\n"
                        +"      backdrop\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"  }\n"
                        +"}"
                }

    if item.c_type == 'peliculas':
        addfilter = {}

        query = {
                "operationName": "PaginationMovie",
                "variables": {"page": page, "limit": items_per_page, "filter": addfilter},
                "query": "query PaginationMovie($sort: SortMovie, $limit: Int, $filter: FilterMoviesInput, $page: Int) {\n"
                        +"  paginationMovie(sort: $sort, limit: $limit, filter: $filter, page: $page) {\n"
                        +"    count\n"
                        +"    pageInfo {\n"
                        +"      hasNextPage\n"
                        +"      currentPage\n"
                        +"      pageCount\n"
                        +"    }\n"
                        +"    items {\n"
                        +"      _id\n"
                        +"      name\n"
                        +"      name_es\n"
                        +"      slug\n"
                        +"      languages\n"
                        +"      release_date\n"
                        +"      poster_path\n"
                        +"      poster\n"
                        +"      backdrop_path\n"
                        +"      backdrop\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"  }\n"
                        +"}"
                }

    return list_all_query(item, query, page)


def list_all_query(item, query, page):
    logger.info()

    itemlist = list()

    data_json = read_api(query)

    if not data_json or not data_json.get('data'):
        return itemlist

    data = data_json['data']

    page_info = False
    content_list = []

    if item.c_type == 'ultimos_episodios':
        content_list = data.get('premiereEpisodes') or []

    if item.c_type == 'search':
        doramas = data.get('searchFullDoramas') or {}
        movies = data.get('searchFullMovies') or {}
        content_list = (doramas.get('items') or []) + (movies.get('items') or [])
        page_info = (doramas.get('pageInfo') or {}).get('hasNextPage') \
                    or (movies.get('pageInfo') or {}).get('hasNextPage')

    if item.c_type == 'peliculas':
        pagination = data.get('paginationMovie') or {}
        content_list = pagination.get('items') or []
        page_info = (pagination.get('pageInfo') or {}).get('hasNextPage')

    if item.c_type in ['doramas', 'TvShows']:
        pagination = data.get('paginationDorama') or {}
        content_list = pagination.get('items') or []
        page_info = (pagination.get('pageInfo') or {}).get('hasNextPage')

    if not content_list:
        return itemlist

    if item.c_type != 'ultimos_episodios':
        languages = get_all_languages()

    for dorama in content_list:
        infoLabels = {}
        item_args = {}

        item_args['channel'] = item.channel
        item_args['url'] = dorama['_id']
        item_args['slug'] = dorama.get('slug') or ''
        
        item_args['context'] = autoplay.context
        if dorama.get('languages'):
            item_args['language'] = get_language_list(languages, dorama['languages'])

        if dorama['__typename'] == "Movie":
            item_args['contentType'] = 'movie'
            item_args['contentTitle'] = dorama['name']
            item_args['title'] = dorama['name']
            item_args['action'] = 'findvideos'
            img_path = dorama.get('poster_path') or dorama.get('backdrop_path') or ''
            release_date = dorama.get('release_date') or ''

            if get_year(release_date):
                infoLabels['year'] = get_year(release_date)
                infoLabels['release_date'] = get_aired(release_date)
                infoLabels['premiered'] = get_aired(release_date)

        elif dorama['__typename'] == "EpisodeMin":
            item_args['contentType'] = 'episode'
            item_args['contentSerieName'] = dorama.get('serie_name') or dorama.get('serie_name_es') or ''
            item_args['action'] = 'findvideos'
            infoLabels['season'] = dorama.get('season_number') or ''
            infoLabels['episode'] = dorama.get('episode_number') or ''
            item_args['title'] = "{}x{} {}".format(infoLabels['season'], infoLabels['episode'], item_args['contentSerieName'])
            img_path = dorama.get('still_path') or ''

            air_date = dorama.get('air_date') or dorama.get('date_string') or ''

            if get_year(air_date):
                infoLabels['year'] = get_year(air_date)
                infoLabels['aired'] = get_aired(air_date)

        else:
            item_args['contentType'] = 'tvshow'
            item_args['contentSerieName'] = dorama['name']
            item_args['title'] = dorama['name']
            item_args['action'] = 'seasons'
            img_path = dorama.get('poster_path') or dorama.get('backdrop_path') or ''
            first_air_date = dorama.get('first_air_date') or ''

            if get_year(first_air_date):
                infoLabels['year'] = get_year(first_air_date)
                infoLabels['aired'] = get_aired(first_air_date)
                infoLabels['premiered'] = get_aired(first_air_date)

        infoLabels['filtro'] = img_path
        item_args['infoLabels'] = infoLabels
        item_args['thumbnail'] = get_thumb_path(img_path)

        new_item = Item(**item_args)

        new_item.context = filtertools.context(new_item, list_language, list_quality)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)
    
    # Paginacion
    if page_info:
        itemlist.append(item.clone(
                                    action="search" if item.c_type == 'search' else "list_all",
                                    title=">> {} {}".format(config.get_localized_string(30992), page + 1),
                                    page=page + 1,
                                    thumbnail=get_thumb("next.png")
                                    ))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []

    templist = seasons(item)

    if not templist:
        return itemlist

    if templist[0].contentSeason:
        for tempitem in templist:
            itemlist += [i for i in seasons(tempitem) if i.action == 'findvideos']
    else:
        itemlist = [i for i in templist if i.action == 'findvideos']

    return itemlist


def seasons(item):
    logger.info()

    season = 1 if not item.contentSeason else item.contentSeason

    query = {"operationName": "detailSeasonExtra",
             "variables": {"slug": item.slug, "season_number": season},
             "query": "query detailSeasonExtra($slug: String!, $season_number: Int!) {\n"
                    +"  listSeasons(sort: NUMBER_ASC, filter: {serie_slug: $slug}) {\n"
                    +"    slug\n"
                    +"    season_number\n"
                    +"    poster_path\n"
                    +"    serie_backdrop_path\n"
                    +"    air_date\n"
                    +"    serie_name\n"
                    +"    trailer\n"
                    +"    backdrop\n"
                    +"    overview\n"
                    +"    _id\n"
                    +"    name\n"
                    +"    emision\n"
                    +"    pause\n"
                    +"    uploading\n"
                    +"    commingSoon\n"
                    +"    __typename\n"
                    +"  }\n"
                    +"  listEpisodes(\n"
                    +"    sort: NUMBER_ASC\n"
                    +"    filter: {serie_slug: $slug, season_number: $season_number}\n"
                    +"  ) {\n"
                    +"    _id\n"
                    +"    name\n"
                    +"    slug\n"
                    +"    serie_name\n"
                    +"    serie_id\n"
                    +"    still_path\n"
                    +"    air_date\n"
                    +"    season_number\n"
                    +"    episode_number\n"
                    +"    languages\n"
                    +"    backdrop\n"
                    +"    __typename\n"
                    +"  }\n"
                    +"}"}

    data_json = read_api(query)
    if not data_json or not data_json.get('data'):
        return []

    itemlist = list()

    seasons_list = data_json['data'].get('listSeasons') or []
    episodes_list = data_json['data'].get('listEpisodes') or []

    # He encontrado alguna serie que venian las temporadas duplicadas
    clean_up_seasons(seasons_list)
    
    if not item.contentSeason and len(seasons_list) > 1:
        for season in seasons_list:
            new_item = item.clone(
                    contentSeason=season['season_number'], 
                    title=(config.get_localized_string(60027) % season['season_number']) if season['season_number'] > 0 else config.get_localized_string(70483),
                    contentPlot=season.get('overview') or '', 
                    thumbnail=get_thumb_path(season.get('poster_path') or season.get('serie_backdrop_path')), 
                    contentType='season'
                )

            itemlist.append(new_item)

        return itemlist

    infoLabels = item.infoLabels.copy()
    for episode in episodes_list:
        try:
            infoLabels['season'] = int(episode['season_number']) or 1
            infoLabels['episode'] = int(episode['episode_number']) or 1
        except Exception:
            continue

        aired = get_aired(episode.get('air_date'))
        if aired:
            infoLabels['aired'] = aired
            if not infoLabels.get('year'):
                infoLabels['year'] = get_year(episode.get('air_date'))

        title = "{0}x{1} Episodio {1}".format(infoLabels['season'], infoLabels['episode'])

        new_item = item.clone(
            title = title,
            url = episode['_id'],
            slug = episode['slug'],
            action = 'findvideos',
            infoLabels = infoLabels,
            contentType = 'episode',
            contentSerieName = item.contentSerieName or episode.get('serie_name') or '',
            thumbnail = get_thumb_path(episode.get('still_path'))
        )

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.videolibrary:
        itemlist.append(
            Item(
                action = "add_serie_to_library",
                channel = item.channel,
                contentSerieName = item.contentSerieName,
                extra = "episodios",
                title = config.get_localized_string(70146),
                url = item.url,
                slug = item.slug
            )
        )

    return itemlist


def clean_up_seasons(seasons_list):
    season_number_set = set()
    for i in seasons_list[:]:
        if i['season_number'] in season_number_set:
            seasons_list.remove(i)
        else:
            season_number_set.add(i['season_number'])


def search(item, texto, **AHkwargs):
    logger.info()

    try:
        texto = texto.strip()
        if not texto:
            return []

        item.texto = texto
        item.c_type = 'search'

        page = item.page or 1

        query = {
                "operationName": "searchFull",
                "variables": {"input": texto, "page": page, "perPage": items_per_page},
                "query": "query searchFull($input: String!, $page: Int, $perPage: Int) {\n"
                        +"  searchFullDoramas(input: $input, page: $page, perPage: $perPage) {\n"
                        +"    count\n"
                        +"    pageInfo {\n"
                        +"      hasNextPage\n"
                        +"    }\n"
                        +"    items {\n"
                        +"      _id\n"
                        +"      name\n"
                        +"      name_es\n"
                        +"      slug\n"
                        +"      languages\n"
                        +"      first_air_date\n"
                        +"      poster_path\n"
                        +"      backdrop_path\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"  }\n"
                        +"  searchFullMovies(input: $input, page: $page, perPage: $perPage) {\n"
                        +"    count\n"
                        +"    pageInfo {\n"
                        +"      hasNextPage\n"
                        +"    }\n"
                        +"    items {\n"
                        +"      _id\n"
                        +"      name\n"
                        +"      name_es\n"
                        +"      slug\n"
                        +"      languages\n"
                        +"      release_date\n"
                        +"      poster_path\n"
                        +"      backdrop_path\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"  }\n"
                        +"}"
                }

        return list_all_query(item, query, page)

    except Exception as e:
        logger.error(str(e))
        return []


def new_episodes(item):
    logger.info()
    
    query = {
            "operationName": "premiereEpisodes",
            "variables": {"limit": 20},
            "query": "query premiereEpisodes($limit: Int!) {\n"
                    +"  premiereEpisodes(limit: $limit) {\n"
                    +"    _id\n"
                    +"    name\n"
                    +"    air_date\n"
                    +"    serie_name\n"
                    +"    serie_name_es\n"
                    +"    slug\n"
                    +"    still_path\n"
                    +"    still_image\n"
                    +"    backdrop\n"
                    +"    date_string\n"
                    +"    overview\n"
                    +"    season_number\n"
                    +"    episode_number\n"
                    +"    __typename\n"
                    +"  }\n"
                    +"}"
            }
    
    item.c_type = 'ultimos_episodios'
    
    return list_all_query(item, query, 1)


def newest(categoria):
    logger.info()
    
    itemlist = []
    item = Item(channel=canonical['channel'])
    
    if categoria == 'series':
        itemlist = new_episodes(item)
    
    return itemlist


def get_online_links(item):
    """Enlaces 'online' (los mismos que muestra el reproductor de la web).

    Llegan envueltos en un token de embedshortener, se decodifican en decode_link().
    """
    
    if item.contentType == 'episode':
        query = {"operationName": "EpisodeLinksOnline",
                 "variables": {"episode_id": item.url},
                 "query": 'query EpisodeLinksOnline($episode_id: ID!) {\n'
                          +'  getEpisodeLinks(id: $episode_id, app: "%s") {\n' % APP_ID
                          +"    links_online {\n"
                          +"      lang\n"
                          +"      link\n"
                          +"      server\n"
                          +"      is_recommended\n"
                          +"    }\n"
                          +"  }\n"
                          +"}"
                 }
        key = 'getEpisodeLinks'
    else:
        query = {"operationName": "MovieLinks",
                 "variables": {"movie_id": item.url},
                 "query": 'query MovieLinks($movie_id: ID!) {\n'
                          +'  getMovieLinks(id: $movie_id, app: "%s") {\n' % APP_ID
                          +"    links_online {\n"
                          +"      lang\n"
                          +"      link\n"
                          +"      server\n"
                          +"      is_recommended\n"
                          +"    }\n"
                          +"  }\n"
                          +"}"
                 }
        key = 'getMovieLinks'
    
    data_json = read_api(query)
    if not data_json or not data_json.get('data'):
        return []
    
    return (data_json['data'].get(key) or {}).get('links_online') or []


def get_detail_links(item):
    """Todos los enlaces guardados del episodio/película (más antiguos y con enlaces directos)."""
    
    if item.contentType == 'episode':
        query = {"operationName": "detailEpisodeLinks",
                 "variables": {"_id": item.url},
                 "query": "query detailEpisodeLinks($_id: ID!) {\n"
                          +"  detailEpisode(id: $_id) {\n"
                          +"    _id\n"
                          +"    links_online {\n"
                          +"      lang\n"
                          +"      link\n"
                          +"      page\n"
                          +"      server\n"
                          +"      is_recommended\n"
                          +"    }\n"
                          +"  }\n"
                          +"}"
                 }
        key = 'detailEpisode'
    else:
        query = {"operationName": "detailMovieLinks",
                 "variables": {"_id": item.url},
                 "query": "query detailMovieLinks($_id: ID!) {\n"
                          +"  detailMovie(id: $_id) {\n"
                          +"    _id\n"
                          +"    links_online {\n"
                          +"      lang\n"
                          +"      link\n"
                          +"      page\n"
                          +"      server\n"
                          +"      is_recommended\n"
                          +"    }\n"
                          +"  }\n"
                          +"}"
                 }
        key = 'detailMovie'
    
    data_json = read_api(query)
    if not data_json or not data_json.get('data'):
        return []
    
    return (data_json['data'].get(key) or {}).get('links_online') or []


def decode_link(link):
    """Extrae la URL real de los enlaces envueltos (https://embedshortener.co/e/<jwt>)."""
    
    if not link or 'embedshortener' not in link:
        return link
    
    try:
        token = link.rstrip('/').rsplit('/', 1)[-1]
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        payload = base64.urlsafe_b64decode(payload)
        if PY3:
            payload = payload.decode('utf-8', 'replace')
        
        data = json.loads(payload)
        real_link = data.get('link') or ''
        real_link += '=' * (-len(real_link) % 4)
        real_link = base64.b64decode(real_link)
        if PY3:
            real_link = real_link.decode('utf-8', 'replace')
        
        return real_link or link
    
    except Exception as e:
        logger.error("No se ha podido decodificar el enlace {}: {}".format(link[:120], str(e)))
        return link


def findvideos(item):
    logger.info()
    itemlist = []
    links = []
    
    for video in get_online_links(item):
        links.append({'link': video.get('link'), 'lang': video.get('lang'),
                      'recommended': bool(video.get('is_recommended'))})
    
    for video in get_detail_links(item):
        links.append({'link': video.get('link'), 'lang': video.get('lang'), 'recommended': False})
    
    if not links:
        return itemlist
    
    content_list = []
    for video in links:
        link = decode_link(video.get('link') or '')
        if not link.startswith('http'):
            continue
        if in_dictlist(content_list, 'link', link):
            continue
        content_list.append({'link': link, 'lang': video.get('lang'),
                             'recommended': video.get('recommended')})
    
    if not content_list:
        return itemlist
    
    logger.info("Enlaces: {}".format([v['link'] for v in content_list]))
    
    languages = get_all_languages()
    content_list = sorted(content_list, key=lambda x: (not x['recommended'], str(x.get('lang') or '')))
    
    for video in content_list:
        itemlist.append(Item(channel=item.channel, title='%s', url=video['link'], action='play', quality='HD',
                             language=get_language_string(languages, video.get('lang')), infoLabels=item.infoLabels))
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    
    # Filtra los enlaces cuyos servidores no fueron resueltos por servertools
    # itemlist = [i for i in itemlist if i.title != "Directo"]
    
    # Un mismo servidor puede venir repetido con varios dominios (do7go/dood.stream...)
    vistos = []
    unicos = []
    for i in itemlist:
        key = (i.server, str(i.language))
        if key in vistos:
            continue
        vistos.append(key)
        unicos.append(i)
    
    # itemlist = unicos
    
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and not item.contentSerieName:
        itemlist.append(Item(channel=item.channel, title=config.get_localized_string(70146),
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))
    
    return itemlist


def in_dictlist(dictlist, key, value):
    logger.info()
    for entry in dictlist:
        if entry[key] == value:
            return True
    return False


def get_all_languages():
    logger.info()
    
    lang_data = get_lang_data()
    
    if lang_data and all(str(lang.get('code_flix') or '').isdigit() for lang in lang_data):
        return lang_data
    
    query = {"operationName": "listLanguages",
            "query": "query listLanguages {\n"
                    +"  listLanguages {\n"
                    +"    name\n"
                    +"    code_flix\n"
                    +"  }\n"
                    +"}"}
    
    data_json = read_api(query)
    if not data_json or not data_json.get('data'):
        return []
    lang_data = data_json['data'].get('listLanguages') or []
    save_lang_data(lang_data)
    
    return lang_data


def get_language_list(languages, code_list):
    if not code_list:
        return []
    
    lang_list = []
    for code in code_list:
        name = get_language_string(languages, code)
        if name and name not in lang_list:
            lang_list.append(name)
    
    return lang_list


def get_language_string(languages, code):
    if not code:
        return ""
    
    code = str(code)
    
    for lang in languages or []:
        if str(lang.get('code_flix')) == code:
            return LANGUAGE_ALIASES.get(lang.get('name'), lang.get('name'))
    
    return LANGUAGE_ALIASES.get(code, "")


def get_lang_data():
    logger.info()
    return jsontools.get_node_from_file(canonical['channel'], TAG_CHANNEL_LANGUAGE_DATA)


def save_lang_data(lang_data):
    logger.info()
    result, json_data = jsontools.update_node(lang_data, canonical['channel'], TAG_CHANNEL_LANGUAGE_DATA)
    return result
