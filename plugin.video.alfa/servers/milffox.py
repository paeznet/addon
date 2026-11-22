# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "<h2>WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
        return False, "[milffox] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global data
    
    if not data:
        data = httptools.downloadpage(page_url).data
    
    bloque = scrapertools.find_single_match(data, r'videoFile:([^;]+);')
    pares = re.findall(r'\[(\d+p)\]([^"\']+)', bloque)
    
    for quality, url in pares:
        url = url.strip().strip(',').strip()
        
        if not url:
            continue
        
        if url.startswith('//'):
            url = 'https:' + url
        elif not url.startswith('http'):
            url = urlparse.urljoin(page_url, url)
        
        try:
            location = httptools.downloadpage(url, headers={'Referer': page_url},
                                              follow_redirects=False,
                                              only_headers=True).headers.get('location', '')
        except Exception as e:
            logger.error("[milffox] no se pudo resolver %s (%s)" % (url, str(e)[:80]))
            location = ''
        
        if location:
            url = location
        
        cabeceras = '|Referer=%s&User-Agent=%s' % (page_url, httptools.get_user_agent())
        video_urls.append(["[milffox] %s" % quality, url + cabeceras])
    
    return video_urls[::-1]
