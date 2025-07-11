# -*- coding: utf-8 -*-
#------------------------------------------------------------

import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import urlparse
from bs4 import BeautifulSoup

canonical = {
             'channel': 'sextvx', 
             'host': config.get_setting("current_host", 'sextvx', default=''), 
             'host_alt': ["https://www.sextvx.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "es/recent/"))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "es/popular/"))
    itemlist.append(Item(channel=item.channel, title="Pornstars" , action="categorias", url=host + "es/pornstars/"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "es/categories/"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ses/results?search_query=%s&r=1" % (host,texto)
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
    matches = soup.find_all('div', class_='video')
    for elem in matches:
        logger.debug(elem)
        t = elem.find('div', class_='thumb-info')
        title = t.a.text.strip()
        cantidad = t.span.text.strip().replace(" videos", "").replace("ondemand_video ", "")
        title = "%s (%s)" %(title, cantidad)
        url = elem.a['href']
        if elem.img.get('alt', ''):
            # title = elem.img['alt']
            thumbnail = elem.img['data-src']
        else:
            thumbnail = elem.img['src']
        url = urlparse.urljoin(item.url,url)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    
    # itemlist.sort(key=lambda x: x.title)
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
    matches = soup.find_all('div', class_='video') ## id = re.compile(r"^div-\d+"
    for elem in matches:
        if not elem.get('id', ''): continue
        url = elem.a['href']
        title = elem.img['alt']
        if "search_query" in item.url:
            thumbnail = elem.img['src']
        else:
            thumbnail = elem.img['data-src']
        time = elem.find('span', class_='duration').next_sibling
        quality = elem.find('span', class_='hd-res')
        if quality:
            quality = quality.text
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time,quality,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        url = urlparse.urljoin(host, url)
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title= "%s" , contentTitle=item.contentTitle, url=item.url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist

def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if soup.find('div', id='video-infos'):
        pornstars = soup.find('div', id='video-infos').find_all('a', href=re.compile("/pornstar/\d+/[A-z0-9-]+"))
        for x , value in enumerate(pornstars):
            pornstars[x] = value['title'].replace(" videos", "")
        pornstar = ' & '.join(pornstars)
        pornstar = " [COLOR cyan]%s" % pornstar
        lista = item.contentTitle.split('[/COLOR]')
        if "[COLOR red]" in item.contentTitle:
            lista.insert (2, pornstar)
        else:
            lista.insert (1, pornstar)
        item.contentTitle = '[/COLOR]'.join(lista)    
    itemlist.append(Item(channel=item.channel, action="play", title= "%s" , contentTitle=item.contentTitle, url=item.url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist
