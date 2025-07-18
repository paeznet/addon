# -*- coding: utf-8 -*-
# -*- Channel Eroticage -*-
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

IDIOMAS = {}
list_language = list(set(IDIOMAS.values()))
list_quality = []
list_quality_movies = []
list_quality_tvshow = []
list_servers = []
forced_proxy_opt = 'ProxySSL'

#  https://www.eroticage.net/  100    https://www.erogarga.com/  

canonical = {
             'channel': 'eroticage', 
             'host': config.get_setting("current_host", 'eroticage', default=''), 
             'host_alt': ["https://www.eroticage.net/"], 
             'host_black_list': [], 
             'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'cf_assistant': False, 'CF_stat': True, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 45
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = ''
tv_path = ''
language = []
url_replace = []


finds = {'find': dict([('find', [{'tag': ['div', 'main'], 'id': ['primary', 'main']}]),
                       ('find_all', [{'tag': ['article'], 'class': [re.compile(r"^post-\d+")]}])]), 
         'categories':dict([('find', [{'tag': ['div', 'main'], 'id': ['primary', 'main']}]),
                            ('find_all', [{'tag': ['article'], 'class': [re.compile(r"^post-\d+")]}])]),
         'search': {}, 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {},
         'next_page_rgx': [['\/page\/\d+', '/page/%s']], 
         'last_page': dict([('find', [{'tag': ['div', 'nav'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-1], 
                                           '@ARG': 'href', '@TEXT': 'page/(\d+)'}])]), 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['article'], 'class': re.compile(r"^post-\d+")}]), 
                             ('find_all', [{'tagOR': ['a'], 'href': True, 'id': 'tracking-url'},
                                           {'tag': ['iframe'], 'src': True}])]),
         'title_clean': [['[\(|\[]\s*[\)|\]]', ''],['(?i)\s*videos*\s*', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'url_replace': [], 
         'profile_labels': {
                            # 'list_all_thumbnail': {'find': [{'tag': ['img','video'], '@ARG': ['data-src','poster']}]},
                           },
         'controls': {'url_base64': False, 'cnt_tot': 30, 'reverse': False, 'profile': 'default'},  ##'jump_page': True, ##Con last_page  aparecerá una línea por encima de la de control de página, permitiéndote saltar a la página que quieras
         'timeout': timeout}
AlfaChannel = DictionaryAdultChannel(host, movie_path=movie_path, tv_path=tv_path, movie_action='play', canonical=canonical, finds=finds, 
                                     idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                     list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                     channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="eroticage" , action="submenu", url= "https://www.eroticage.net/", chanel="eroticage", thumbnail = "https://i.postimg.cc/dVhYnmVg/eroticage-logo.jpg")) 
    itemlist.append(Item(channel=item.channel, title="erogarga" , action="submenu", url= "https://www.erogarga.com/", chanel="erogarga", thumbnail = "https://i.postimg.cc/wvtXxBg1/erogarga.png"))
    # itemlist.append(Item(channel=item.channel, title="" , action="submenu", url= "", chanel="", thumbnail = ""))
    # itemlist.append(Item(channel=item.channel, title="" , action="submenu", url= "", chanel="", thumbnail = ""))
    # itemlist.append(Item(channel=item.channel, title="" , action="submenu", url= "", chanel="", thumbnail = ""))
    # itemlist.append(Item(channel=item.channel, title="" , action="submenu", url= "", chanel="", thumbnail = ""))
    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    
    config.set_setting("current_host", item.url, item.chanel)
    AlfaChannel.host = item.url
    AlfaChannel.canonical.update({'channel': item.chanel, 'host': AlfaChannel.host, 'host_alt': [AlfaChannel.host]})

    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="list_all", url=item.url + "page/1/?filter=latest", chanel=item.chanel))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="list_all", url=item.url + "page/1/?filter=most-viewed", chanel=item.chanel))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="list_all", url=item.url + "page/1/?filter=popular", chanel=item.chanel))
    itemlist.append(Item(channel=item.channel, title="Mas largo" , action="list_all", url=item.url + "page/1/?filter=longest", chanel=item.chanel))
    if "eroticage" in item.chanel:
        itemlist.append(Item(channel=item.channel, title="Año" , action="section", url=item.url + "categories/", extra="año", chanel=item.chanel))
        itemlist.append(Item(channel=item.channel, title="Pais" , action="section", url=item.url, extra="Pais", chanel=item.chanel))
        itemlist.append(Item(channel=item.channel, title="Pornstars" , action="section", url=item.url + "actors/page/1/", extra="PornStar", chanel=item.chanel))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="section", url=item.url + "tags/", extra="Categorias", chanel=item.chanel))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=item.url, chanel=item.chanel))
    
    return itemlist


def section(item):
    logger.info()
    
    findS = finds.copy()
    findS['url_replace'] = [['(\/(?:categories|channels|models|pornstars|actor)\/[^$]+$)', r'\1?filter=latest']]
    if item.extra == 'Categorias':
        findS['categories'] = dict([('find', [{'tag': ['div'], 'class': ['categories-list']}]),
                                    ('find_all', [{'tag': ['a'], 'class': ['tag-cloud-link']}])])
    if item.extra == 'Pais':
        findS['categories'] = dict([('find', [{'tag': ['li'], 'id': ['menu-item-4967']}]),
                                    ('find_all', [{'tag': ['a'], 'href': True}])])

    return AlfaChannel.section(item, finds=findS, **kwargs)


def list_all(item):
    logger.info()
    
    findS = finds.copy()
    if "eroticage" in item.chanel:
        findS['controls']['cnt_tot'] = 25
        findS['profile_labels']['list_all_thumbnail'] = {'find': [{'tag': ['img','video'], '@ARG': ['data-src','poster']}]}
    
    return AlfaChannel.list_all(item, finds=findS, **kwargs)


def findvideos(item):
    logger.info()
    
    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=None, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def play(item):
    logger.info()
    itemlist = []
    
    soup = AlfaChannel.create_soup(item.url, **kwargs)
    if soup.find_all('a', href=re.compile(r"/actor/[a-z0-9-]+")):
        pornstars = soup.find_all('a', href=re.compile(r"/actor/[a-z0-9-]+"))
        for x, value in enumerate(pornstars):
            pornstars[x] = value.get_text(strip=True)
        pornstar = ' & '.join(pornstars)
        pornstar = AlfaChannel.unify_custom('', item, {'play': pornstar})
        lista = item.contentTitle.split('[/COLOR]')
        pornstar = pornstar.replace('[/COLOR]', '')
        pornstar = ' %s' %pornstar
        if AlfaChannel.color_setting.get('quality', '') in item.contentTitle:
            lista.insert (2, pornstar)
        else:
            lista.insert (1, pornstar)
        item.plot = '[/COLOR]'.join(lista)
        
    # matches = soup.find('div', class_='responsive-player')
    # if matches.find('video'):
        # url = matches.source['src']
    # else:
        # url = matches.iframe['src']
    url = soup.find('meta', itemprop='embedURL')['content']
    if "play.php" in url:
        vid = url.split('?vid=')[-1]
        post_url = url.split('play.php')[0]
        post_url += "ajax_sources.php"
        post = {'vid': vid, 'alternative': 'spankbang', 'ord': '0'}
        from core import httptools
        data = httptools.downloadpage(post_url, post=post).json
        url = data['source'][0]['file']
    else:
        url = url
    if not "meta" in url:
        itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=url, plot=item.plot ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    return itemlist


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    # item.url = "%sbuscar/?q=%s&sort_by=video_viewed&from_videos=1" % (host, texto.replace(" ", "+"))
    item.url = "%s?s=%s&filter=latest" % (host, texto.replace(" ", "+"))
    
    try:
        if texto:
            item.c_type = "search"
            item.texto = texto
            return list_all(item)
        else:
            return []
    
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
