# -*- coding: utf-8 -*-
#------------------------------------------------------------
from core import urlparse as alfa_urlparse
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import urlparse
from bs4 import BeautifulSoup
from core import jsontools as json
from modules import autoplay

list_quality = ['default']
list_servers = []


########  PANDAMOVIE


# https://playpornfree.org/   https://streamporn.pw/  https://mangoporn.net/   https://watchfreexxx.net/   https://losporn.org/  https://xxxstreams.me/  https://speedporn.net/
# pandamovie https://watchpornfree.info  https://xxxparodyhd.net  http://www.veporns.com  http://streamporno.eu
# https://www.netflixporno.net   https://xxxscenes.net   https://mangoporn.net   https://speedporn.net  https://streamporn.nl/

canonical = {
             'channel': 'playpornx', 
             'host': config.get_setting("current_host", 'playpornx', default=''), 
             'host_alt': ["https://watchfreexxx.net/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Ultimas", action="lista", url=alfa_urlparse.build_url(host, 'page/1', query='filter=latest')))
    itemlist.append(Item(channel=item.channel, title="Mas Vistas", action="lista", url=alfa_urlparse.build_url(host, 'page/1', query='filter=most-viewed')))
    itemlist.append(Item(channel=item.channel, title="Mejor Valorada", action="lista", url=alfa_urlparse.build_url(host, 'page/1', query='filter=popular')))
    itemlist.append(Item(channel=item.channel, title="Mas Larga", action="lista", url=alfa_urlparse.build_url(host, 'page/1', query='filter=longest')))
    
    itemlist.append(Item(channel=item.channel, title="Year", action="catalogo", url=alfa_urlparse.build_url(host, 'release-year')))
    itemlist.append(Item(channel=item.channel, title="Canal", action="catalogo", url=alfa_urlparse.build_url(host, 'studios', query='sort=pop')))
    itemlist.append(Item(channel=item.channel, title="Pornstar", action="catalogo", url=alfa_urlparse.build_url(host, 'pornstars', query='sort=pop')))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="categorias", url=alfa_urlparse.build_url(host, 'genres')))
    
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=alfa_urlparse.build_url(item.url, query='filter=latest')))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=alfa_urlparse.build_url(item.url, query='filter=most-viewed')))
    itemlist.append(Item(channel=item.channel, title="Mas valorados" , action="lista", url=alfa_urlparse.build_url(item.url, query='filter=popular')))
    itemlist.append(Item(channel=item.channel, title="Mas Largo" , action="lista", url=alfa_urlparse.build_url(item.url, query='filter=longest')))
    itemlist.append(Item(channel=item.channel, title="Pornstars" , action="categorias", url=alfa_urlparse.build_url(item.url, 'pornstars/')))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=alfa_urlparse.build_url(item.url, 'studios/')))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=alfa_urlparse.build_url(host, 'genres/')))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=item.url))
    return itemlist

def search(item, texto):
    logger.info()
    _url_query_texto = texto
    texto = texto.replace(" ", "+")
    item.url = alfa_urlparse.build_url(item.url, query=[('s', u'{}'.format(_url_query_texto)), ('filter', 'latest')])
    try:
        return lista(item)
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url)
    matches = soup.find('div', class_='chips').find_all('a')
    
    for elem in matches:
        url = elem['href']
        
        title = elem.text.strip()
        if elem.small:
            cantidad = elem.small.text.strip()
            title = title.replace(cantidad, '')
            title = "%s (%s)" %(title, cantidad)
        
        plot = ""
        thumbnail = ""
        if elem.img:
            thumbnail = elem.img.get('src', '')
        if not url.startswith("https"):
            url = "https:%s" % url
        if "#" not in url:
            itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                                 thumbnail=thumbnail, plot=plot))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url)
    matches = soup.find('div', class_='tgrid').find_all('a')
    
    for elem in matches:
        url = elem['href']
        
        title = elem.b.text.strip()
        if elem.small:
            cantidad = elem.small.text.strip()
            title = "%s (%s)" %(title, cantidad)
        
        plot = ""
        thumbnail = ""
        if elem.img:
            thumbnail = elem.img.get('src', '')
        if not url.startswith("https"):
            url = "https:%s" % url
        if "#" not in url:
            itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                                 thumbnail=thumbnail, plot=plot))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(Item(channel=item.channel, action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('article', class_='card')
    for elem in matches:
        # logger.debug(elem)
        thumbnail = ""
        url = elem.a['href']
        title = elem.find(class_='card__t').text.strip()
        thumbnail = elem.img.get('src', '').replace("amp;", "")
        if "svg" in thumbnail and elem.img.get('data-lazy-src', ''):
            thumbnail = elem.img['data-lazy-src'].replace("amp;", "")
        elif elem.img.get('data-src', ''):
            thumbnail = elem.img['data-src'].replace("amp;", "")
        year = elem.find(class_='card__q')
        time = elem.find(class_='card__dur')
        if time:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time.text.strip(),title)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    video_urls = []
    soup = create_soup(item.url)
    pornstars = soup.find('div', class_='cn__body').find_all('a', href=re.compile("/(:?pornstar|pornstars|actor)/"))
    for x , value in enumerate(pornstars):
        pornstars[x] = value.text.strip()
    pornstar = ' & '.join(pornstars)
    if "N/A" not in pornstar:
        pornstar = "[COLOR cyan]%s[/COLOR]" % pornstar
    else:
        pornstar = ""
    plot = pornstar
    
    data = soup.section['data-servers']
    JSONData = json.load(data)
    
    for elem in JSONData:
        url = elem['u']
        itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', plot=plot, language='VO',contentTitle = item.contentTitle))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

