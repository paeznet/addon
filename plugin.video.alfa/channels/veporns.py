# -*- coding: utf-8 -*-
# -*- Channel UltraHorny -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAdultChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay

IDIOMAS = AlfaChannelHelper.IDIOMAS_A
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES_A
list_quality_tvshow = []
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS_A
forced_proxy_opt = 'ProxySSL'

''' CANAL ANTIGUA OUT pages
    gameofporn  veporns  https://www.veporno.net  https://www.fxporn.net      http://www.veporns.com    '''

#  https://veporn.com/  https://ultrahorny.com/   https://eporner.xxx/
# https://pornoflix.com/  

canonical = {
             'channel': 'veporns', 
             'host': config.get_setting("current_host", 'veporns', default=''), 
             'host_alt': ["https://veporn.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = ''
tv_path = ''
language = []
url_replace = []

finds = {'find': {'find_all': [{'tag': ['article'], 'class':['loop-post']}]},
         'categories': {'find_all': [{'tag': ['div', 'article'], 'class': ['ctgr', 'pstr']}]}, 
         'search': {}, 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {},
         'next_page_rgx': [['\/page\/\d+', '/page/%s/'], ['&page=\d+', '&page=%s']], 
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['nav-links']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-2], '@ARG': 'href', '@TEXT': 'page/(\d+)'}])]), 
         'plot': {}, 
         'findvideos': {},
         'title_clean': [['[\(|\[]\s*[\)|\]]', ''],['(?i)\s*videos*\s*', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'url_replace': [], 
         'controls': {'url_base64': False, 'cnt_tot': 30, 'reverse': False, 'profile': 'default'}, 
         'timeout': timeout}
AlfaChannel = DictionaryAdultChannel(host, movie_path=movie_path, tv_path=tv_path, movie_action='play', canonical=canonical, finds=finds, 
                                     idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                     list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                     channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)

def mainlist(item):
    logger.info()

    itemlist = []
    
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="list_all", url=host + "?order=newest"))
    itemlist.append(Item(channel=item.channel, title="Mas visto" , action="list_all", url=host + "?order=views"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="list_all", url=host + "?order=rating"))
    itemlist.append(Item(channel=item.channel, title="Mas comentado" , action="list_all", url=host + "?order=comments"))
    itemlist.append(Item(channel=item.channel, title="Mas largo" , action="list_all", url=host + "?order=longest"))
    itemlist.append(Item(channel=item.channel, title="Pornstars", action="section", url=host + "pornstars/page/1", extra="Pornstar"))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="section", url=host + "categories/", extra="Categorias"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))

    return itemlist


def section(item):
    logger.info()
    
    findS = finds.copy()
    
    if "Categorias" in item.extra:
        findS['controls']['cnt_tot'] = 9999
    if "Pornstar" in item.extra:
        findS['controls']['cnt_tot'] = 40
    
    return AlfaChannel.section(item, finds=findS, matches_post=section_matches, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        try:
            
            elem_json['url'] = elem.get("href", '') or elem.a.get("href", '')
            elem_json['title'] = elem.a.get('data-mxptext', '') or elem.a.get('title', '') \
                                                                or (elem.img.get('alt', '') if elem.img else '') \
                                                                or elem.a.get_text(strip=True)
            if elem.img: elem_json['thumbnail'] = elem.img.get('data-thumb_url', '') or elem.img.get('data-original', '') \
                                                                                     or elem.img.get('data-src', '') \
                                                                                     or elem.img.get('src', '')
            elem_json['cantidad'] = elem.p.get_text(strip=True)
            # elem_json['cantidad'] = elem.find(class_=['fwb']).get_text(strip=True)
        
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
        matches.append(elem_json.copy())

    return matches


def list_all(item):
    logger.info()
    
    findS = finds.copy()
    
    return AlfaChannel.list_all(item, finds=findS, matches_post=list_all_matches, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        
        try:
            elem_json['url'] = elem.a.get('href', '')
            elem_json['title'] = elem.h2.get_text(strip=True)
            # elem_json['title'] = elem.a.get('title', '') \
                                 # or elem.a.get_text(strip=True) \
                                 # or (elem.img.get('alt', '') if elem.img else '')
            elem_json['thumbnail'] = elem.img.get('data-original', '') \
                                     or elem.img.get('data-src', '') \
                                     or elem.img.get('src', '')
            elem_json['stime'] = elem.find('i', class_='fa-clock').parent.get_text(strip=True)
            # elem_json['quality'] = elem.find('div', title='Quality').get_text(strip=True) if elem.find('div', title='Quality') else ''
        
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
        matches.append(elem_json.copy())
    
    return matches


def findvideos(item):
    logger.info()
    
    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=None, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def play(item):
    logger.info()
    itemlist = []
    
    soup = AlfaChannel.create_soup(item.url, **kwargs)
    
    pornstars = soup.find_all('a', href=re.compile("/pornstar/[A-z0-9- ]+/"))
    for x , value in enumerate(pornstars):
        pornstars[x] = value.text.strip()
    pornstar = ' & '.join(pornstars)
    pornstar = AlfaChannel.unify_custom('', item, {'play': pornstar})
    lista = item.contentTitle.split('[/COLOR]')
    pornstar = pornstar.replace('[/COLOR]', '')
    pornstar = ' %s' %pornstar
    lista.insert (1, pornstar)
    item.contentTitle = '[/COLOR]'.join(lista)
    
    if soup.find('div', class_='bx-video').get('iframe', ''):
        item.url = soup.find('div', class_='bx-video').iframe['src']
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    return itemlist


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    item.url = "%spage/1/?s=%s" % (host, texto.replace(" ", "+"))
    
    try:
        if texto:
            item.c_type = "search"
            item.extra="Search"
            item.texto = texto
            return list_all(item)
        else:
            return []
    
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
