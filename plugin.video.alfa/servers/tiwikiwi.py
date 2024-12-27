# Conector tiwikiwi By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}
# chems https://media.cm/wcjxurq8sqtz  error 403


# https://filemooon.link/e/mlx76kltz6tn    
# https://fle-rvd0i9o8-moo.com/ptsd/mlx76kltz6tn

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, server
    if "|Referer" in page_url or "|referer" in page_url:
        url, referer = page_url.split("|")
        referer = referer.replace('Referer=', '').replace('referer=', '')
        kwargs['headers'] = {
            'Referer': referer,
            'Sec-Fetch-Dest': 'iframe',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site'
        }
        datos = httptools.downloadpage(url, **kwargs).data
        page_url = scrapertools.find_single_match(datos, '<iframe src="([^\\?]+)')
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    server = scrapertools.get_domain_from_url(page_url).split(".")[-2]
    if response.code == 404 or "not found" in response.data:
        return False,  "[%s] El fichero no existe o ha sido borrado" %server
    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    try:
        # enc_data = scrapertools.find_single_match(data, "type='text/javascript'>(eval.*?)?\s+</script>")
        enc_data = scrapertools.find_multiple_matches(data, "text/javascript(?:'|\")>(eval.*?)</script>")
        dec_data = jsunpack.unpack(enc_data[-1])
    except Exception:
        dec_data = data
    # sources = 'file:"([^"]+)",label:"([^"]+)"'
    sources = 'sources\:\s*\[\{(?:file|src):"([^"]+)"'
    try:
        matches = re.compile(sources, re.DOTALL).findall(dec_data)
        for url in matches:
            video_urls.append(['[%s] m3u' %server , url])
    except Exception:
        pass
    return video_urls
