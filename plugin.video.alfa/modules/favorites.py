# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Lista de vídeos favoritos
# ------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib                                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                                               # Usamos el nativo de PY2 que es más rápido

import time
import xbmc
from core import filetools
from core import scrapertools
from core.item import Item
from core.jsontools import json
from platformcode import config, logger
from platformcode import platformtools

# Fijamos la ruta a favourites.xml
if config.is_xbmc():

    FAVOURITES_PATH = filetools.translatePath("special://profile/favourites.xml")
else:
    FAVOURITES_PATH = filetools.join(config.get_data_path(), "favourites.xml")


def mainlist(item):
    logger.info()
    itemlist = []

    for name, thumb, data in read_favourites():
        if "plugin://plugin.video.%s/?" % config.PLUGIN_NAME in data:
            # Windows usa la entidad html &quot; para las comillas, Android no. 
            # Así que me aseguro de decodificar las comillas para normalizar.
            data = data.replace("&quot;", '"')
            url = scrapertools.find_single_match(data, 'plugin://plugin.video.%s/\?([^"]*)' % config.PLUGIN_NAME)
            item = Item().fromurl(url)
            item.title = name
            item.thumbnail = thumb
            item.isFavourite = True

            if type(item.context) == str:
                item.context = item.context.split("|")
            elif type(item.context) != list:
                item.context = []

            item.context.extend([{"title": config.get_localized_string(30154),  # "Quitar de favoritos"
                                  "action": "delFavourite",
                                  "module": "favorites",
                                  "from_title": item.title},
                                 {"title": config.get_localized_string(70278),  # "Renombrar"
                                  "action": "renameFavourite",
                                  "module": "favorites",
                                  "from_title": item.title}
                                 ])
            # logger.debug(item.tostring('\n'))
            itemlist.append(item)

    return itemlist


def read_favourites():
    logger.info()
    favourites_list = []
    if filetools.exists(FAVOURITES_PATH):
        data = filetools.read(FAVOURITES_PATH)

        matches = scrapertools.find_multiple_matches(data, "<favourite([^<]*)</favourite>")
        for match in matches:
            name = scrapertools.find_single_match(match, 'name="([^"]*)')
            thumb = scrapertools.find_single_match(match, 'thumb="([^"]*)')
            data = scrapertools.find_single_match(match, '[^>]*>([^<]*)')
            favourites_list.append((name, thumb, data))

    return favourites_list


def save_favourites(favourites_list):
    logger.info()
    raw = '<favourites>' + chr(10)
    for name, thumb, data in favourites_list:
        raw += '    <favourite name="%s" thumb="%s">%s</favourite>' % (name, thumb, data) + chr(10)
    raw += '</favourites>' + chr(10)

    return filetools.write(FAVOURITES_PATH, raw)


def get_favourite(item):
    logger.info()
    fav_item = dict()
    for favourite in get_favourites():
        if favourite['title'] == item.from_title:
            fav_item = favourite
            break

    return fav_item


def add_remove_favourite(item):
    logger.info()
    # Comportamiento de Favourites.AddFavourite : Si existe el item se borra, si no existe se añade
    if item.isFavourite:
        favourite = get_favourite(item)
    else:
        favourite = {
          "title": item.title,
          "type": "window",
          "window": "10025",
          "windowparameter": "plugin://plugin.video.%s/?" % config.PLUGIN_NAME + item.tourl().replace('%3D','%3d'),
          "thumbnail": item.thumbnail
        }

    request = {
      "jsonrpc": "2.0",
      "method": "Favourites.AddFavourite",
      "params": favourite,
      "id": 1
    }

    return json.loads(xbmc.executeJSONRPC(json.dumps(request)))


def get_favourites():
    logger.info()
    request = {
      "jsonrpc": "2.0",
      "method": "Favourites.GetFavourites",
      "params": {
        "properties": ["path","window","windowparameter","thumbnail"]
      },
      "id": 1
    }

    return json.loads(xbmc.executeJSONRPC(json.dumps(request)))['result']['favourites']


def addFavourite(item):
    logger.info()
    response = add_remove_favourite(item)
    if response['result'] == 'OK':
        platformtools.dialog_ok(config.get_localized_string(30102), item.title,
                                config.get_localized_string(30108))  # 'se ha añadido a favoritos'


def delFavourite(item):
    logger.info()
    response = add_remove_favourite(item)
    if response['result'] == 'OK':
        platformtools.dialog_ok(config.get_localized_string(30102), item.from_title,
                                config.get_localized_string(30105).lower())  # 'Se ha quitado de favoritos'
        platformtools.itemlist_refresh()


def renameFavourite(item):
    logger.info()
    # logger.debug(item.tostring('\n'))

    # Buscar el item q queremos renombrar en favourites.xml
    favourites_list = read_favourites()
    for i, fav in enumerate(favourites_list):
        if fav[0] == item.from_title:
            # abrir el teclado
            new_title = platformtools.dialog_input(item.from_title, item.title)
            if new_title:
                favourites_list[i] = (new_title, fav[1], fav[2])
                if save_favourites(favourites_list):
                    platformtools.dialog_ok(config.get_localized_string(30102), item.from_title,
                                            "se ha renombrado como:", new_title)  # 'Se ha quitado de favoritos'
                    platformtools.itemlist_refresh()


##################################################
# Funciones para migrar favoritos antiguos (.txt)
def readbookmark(filepath):
    logger.info()

    bookmarkfile = filetools.file_open(filepath)

    lines = bookmarkfile.readlines()

    try:
        titulo = urllib.unquote_plus(lines[0].strip())
    except:
        titulo = lines[0].strip()

    try:
        url = urllib.unquote_plus(lines[1].strip())
    except:
        url = lines[1].strip()

    try:
        thumbnail = urllib.unquote_plus(lines[2].strip())
    except:
        thumbnail = lines[2].strip()

    try:
        server = urllib.unquote_plus(lines[3].strip())
    except:
        server = lines[3].strip()

    try:
        plot = urllib.unquote_plus(lines[4].strip())
    except:
        plot = lines[4].strip()

    # Campos contentTitle y canal añadidos
    if len(lines) >= 6:
        try:
            contentTitle = urllib.unquote_plus(lines[5].strip())
        except:
            contentTitle = lines[5].strip()
    else:
        contentTitle = titulo

    if len(lines) >= 7:
        try:
            canal = urllib.unquote_plus(lines[6].strip())
        except:
            canal = lines[6].strip()
    else:
        canal = ""

    bookmarkfile.close()

    return canal, titulo, thumbnail, plot, server, url, contentTitle


def check_bookmark(readpath):
    # Crea un listado con las entradas de favoritos
    itemlist = []

    for fichero in sorted(filetools.listdir(readpath)):
        # Ficheros antiguos (".txt")
        if fichero.endswith(".txt"):
            # Esperamos 0.1 segundos entre ficheros, para que no se solapen los nombres de archivo
            time.sleep(0.1)

            # Obtenemos el item desde el .txt
            canal, titulo, thumbnail, plot, server, url, contentTitle = readbookmark(filetools.join(readpath, fichero))
            if canal == "":
                canal = "favorites"
            item = Item(channel=canal, action="play", url=url, server=server, title=contentTitle, thumbnail=thumbnail,
                        plot=plot, fanart=thumbnail, contentTitle=contentTitle, folder=False)

            filetools.rename(filetools.join(readpath, fichero), fichero[:-4] + ".old")
            itemlist.append(item)

    # Si hay Favoritos q guardar
    if itemlist:
        favourites_list = read_favourites()
        for item in itemlist:
            data = "ActivateWindow(10025,&quot;plugin://plugin.video.alfa/?" + item.tourl() + "&quot;,return)"
            favourites_list.append((item.title, item.thumbnail, data))
        if save_favourites(favourites_list):
            logger.debug("Conversion de txt a xml correcta")


# Esto solo funcionara al migrar de versiones anteriores, ya no existe "bookmarkpath"
try:
    if config.get_setting("bookmarkpath") != "":
        check_bookmark(config.get_setting("bookmarkpath"))
    else:
        logger.info("No existe la ruta a los favoritos de versiones antiguas")
except:
    pass
