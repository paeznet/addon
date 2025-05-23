# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from modules import autoplay
from platformcode import config, logger, platformtools
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import urlparse
from bs4 import BeautifulSoup

list_servers = ["directo", "fembed", "mixdrop", "doodstream", "clipwatching", "cloudvideo"]
list_quality = []

canonical = {
             'channel': 'holedk', 
             'host': config.get_setting("current_host", 'holedk', default=''), 
             'host_alt': ["https://www.holedk.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

        #NETU  CloudflareChallengeError: Detected a Cloudflare version 2 Captcha challenge

def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)

    # itemlist.append(Item(channel=item.channel, title="Videos" , action="lista", url=host + "/genre/videos/")) #NETU
    itemlist.append(Item(channel=item.channel, title="Peliculas" , action="lista", url=host))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))

    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%sindex.php?s=%s" % (host,texto)
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
    soup = create_soup(item.url).find('ul', class_='nav')
    if "Canal" in item.title:
        matches = soup.find_all('a', href=re.compile(r"^/director/"))
    else:
        matches = soup.find_all('a', href=re.compile(r"^/genre/"))
    for elem in matches:
        url = elem['href']
        title = elem.text.strip()
        thumbnail = ""
        url = urlparse.urljoin(item.url,url)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    itemlist.sort(key=lambda x: x.title)
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
    soup = create_soup(item.url, referer=host)
    
    if "videos" in item.url:
        matches = soup.find_all('div', class_='cont_videos')
    else:
        matches = soup.find_all('div', class_='cont_peliculas')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['src']
        if "videos" in item.url:
            plot = ""
        else:
            plot = elem.find('div', class_='info').text.strip()
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('span', class_='current')
    if next_page and next_page.find_next_sibling("a"):
        next_page = next_page.find_next_sibling("a")['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', id=re.compile(r"^tab\d+"))
    for elem in matches:
        text = elem.text.strip()
        ser = scrapertools.find_single_match(text, '(\w+)\(')
        id = scrapertools.find_single_match(text, '\w+\("([^"]+)"')
        if "doo" in ser:
            url = "https://dood.to/e/%s" % id
            itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=url))
        elif "tape" in ser:
            url = "https://streamtape.com/e/%s" % id
            itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=url))
        elif "voe" in ser:
            url = "https://voe.sx/e/%s" % id
            itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=url))
        elif "moon" in ser:
            url = "https://filemoon.to/e/%s" % id
            itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=url))
        elif "gua" in ser:
            url = "https://listeamed.net/e/%s" % id
            itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=url))
        elif "mix" in ser:
            url = "https://mixdrop.is/e/%s" % id
            itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=url))
        elif "lulu" in ser:
            url = "https://lulustream.com/e/%s" % id
            itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=url))
        elif "ntu" in ser:
            continue
        else:
            platformtools.dialog_ok("Server Nuevo", "Server nuevo en este canal [%s]" %ser)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

