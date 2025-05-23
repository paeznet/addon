# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vidmoly By Alfa development Group
# --------------------------------------------------------
import re
from core import httptools
from core import scrapertools
from platformcode import logger
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}

# Error 403  captcha
# NO PIDE el captcha  https://vidmoly.me/\\1.html
# https://vidmoly.me/embed-15e4ac1yvzfm.html  >>>  https://vidmoly.me/w/15e4ac1yvzfm
#

def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url, timeout=30)
    data = response.data
    if response.code == 403:
        return False, "[vidmoly] Error"
    if response.code == 404 or "Please wait" in data or "/notice.php" in data:
        return False, "[vidmoly] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    url, quality = scrapertools.find_single_match(data, '\{file:"([^"]+)"\}.*?label:\s"([^"]+)"')
    url += "|Referer=%s" % page_url
    video_urls.append(['[vidmoly] m3u8 %s' %quality, url])

    # mp4_sources = re.compile('\{file:"([^"]+)",label:"([^"]+)"', re.DOTALL).findall(data)

    # for url, qlty in mp4_sources:
        # video_urls.append(['%s [vidmoly]' % qlty, url])

    return video_urls
