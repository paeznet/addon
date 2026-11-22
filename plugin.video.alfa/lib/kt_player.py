# -*- coding: utf-8 -*-
# --------------------------------------------------------
# decode kt_player Alfa-addon
# --------------------------------------------------------

from __future__ import division
from __future__ import absolute_import
from builtins import range
import base64
import binascii
import hashlib
import hmac
import json
import re
import struct
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode


# --------------------------------------------------------
# generate_mp4: los sitios kt_player que alojan el video en OK.RU no dejan la URL buena
# en la pagina. Dejan una llamada
#     generate_mp4('<config cifrada en base64>', '<password>', '<video_id OK.RU>', '<id del sitio>')
# La config es un JSON {"ciphertext", "iv", "salt", "iterations"}: con PBKDF2-SHA512(password,
# salt) se saca la clave AES-256 y al descifrar en CBC sale la session_key de OK.RU. Con esa
# session_key se pide video.get a la API y devuelve las URLs reales (okcdn.ru).
# Medido el 2026-11-17 con fulleroticmovies: video.get responde 200 con url_mobile/url_tiny/
# url_low/url_medium y el mp4 se descarga (Content-Type video/mp4, caja ftyp correcta).
# --------------------------------------------------------

OKRU_APP_KEY = 'CBAFJIICABABABABA'
OKRU_CAMPOS = ('video.url_tiny,video.url_low,video.url_high,video.url_medium,'
               'video.url_quadhd,video.url_mobile,video.url_ultrahd,video.url_fullhd,')

# nombre del campo en la respuesta de OK.RU -> etiqueta de calidad
MAPA_CALIDADES_OKRU = {'mobile': '144p', 'tiny': '240p', 'low': '360p', 'medium': '480p',
                       'high': '720p', 'fullhd': '1080p', 'quadhd': '1440p', 'ultrahd': '2160p'}

_RX_GENERATE_MP4 = re.compile(
    r"generate_mp4\s*\(\s*(['\"])(?P<payload>.+?)\1\s*,\s*(['\"])(?P<clave>.+?)\3\s*,"
    r"\s*(['\"])(?P<vids>.+?)\5(?:\s*,\s*(['\"])(?P<vid_site>.+?)\7)?", re.S)


def saca_generate_mp4(data):
    """Saca de la pagina los argumentos de generate_mp4().

    Devuelve (payload, clave, vids) o None si la pagina no usa generate_mp4.
    """
    if not data:
        return None
    if isinstance(data, bytes):
        data = data.decode('utf-8', 'replace')
    match = _RX_GENERATE_MP4.search(data)
    if not match:
        return None
    return match.group('payload'), match.group('clave'), match.group('vids')


def _pbkdf2_sha512(clave, salt, dklen, iteraciones):
    try:
        return hashlib.pbkdf2_hmac('sha512', clave, salt, iteraciones, dklen)
    except AttributeError:
        # Respaldo para Python sin pbkdf2_hmac: PBKDF2-HMAC-SHA512 a mano (RFC 2898)
        resultado = b''
        bloque = 1
        while len(resultado) < dklen:
            u = hmac.new(clave, salt + struct.pack('>I', bloque), hashlib.sha512).digest()
            acumulado = bytearray(u)
            for _ in range(iteraciones - 1):
                u = hmac.new(clave, u, hashlib.sha512).digest()
                for i in range(len(acumulado)):
                    acumulado[i] ^= u[i]
            resultado += bytes(acumulado)
            bloque += 1
        return resultado[:dklen]


def _aes_cbc_decrypt(clave, iv, ciphertext):
    import pyaes
    descifrador = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(clave, iv=iv))
    # pyaes devuelve los bytes segun van saliendo y quita el relleno PKCS7 al cerrar con feed()
    claro = bytes(descifrador.feed(ciphertext)) + bytes(descifrador.feed())
    return claro


def descifra_token(payload, clave):
    """Descifra la config de generate_mp4 y devuelve la session_key de OK.RU ('' si falla)."""
    try:
        datos = json.loads(base64.b64decode(payload))
        salt = binascii.unhexlify(datos['salt'])
        iv = binascii.unhexlify(datos['iv'])
        ciphertext = base64.b64decode(datos['ciphertext'])
        iteraciones = int(datos.get('iterations', 999))
        if iteraciones < 1 or iteraciones > 10000:
            return ''
        clave_aes = _pbkdf2_sha512(clave.encode('utf-8'), salt, 32, iteraciones)
        return _aes_cbc_decrypt(clave_aes, iv, ciphertext).decode('utf-8', 'replace').strip()
    except Exception:
        return ''


def url_okru(token, vids):
    """URL de la API video.get de OK.RU para la session_key y el/los video_id dados."""
    if not isinstance(vids, (list, tuple)):
        vids = [vids]
    parametros = [('application_key', OKRU_APP_KEY), ('fields', OKRU_CAMPOS),
                  ('method', 'video.get'), ('session_key', token),
                  ('vids', ','.join([u'{}'.format(v) for v in vids]))]
    return u'https://api.ok.ru/fb.do?%s' % urlencode(parametros)


def decode(video_url, license_code, _size=16):
    d = video_url.split("/")[1:]
    h = d[6][:2 * _size]

    v = e(license_code, _size)
    if v and h:
        t = h

        u = len(h)-1
        for u in range(u, -1, -1):
            ind = u

            k = u
            for k in range(k, len(v)):
               ind += int(v[k])

            while ind >= len(h):
               ind -= len(h)

            a = ""
            for i in range(len(h)):
                if i == u:
                   a += h[ind]
                elif i == ind:
                   a += h[u]
                else:
                   a += h[i]
            h = a

        d[6] = d[6].replace(t, h);
        d.pop(0);
        video_url = "/".join(d);

    return video_url

def e(license_code, _size):
    p = license_code
    d = p
    s = ""

    for i in range(1,len(d)):
        if d[i]:
            s += str(d[i])
        else:
            s += str(1)
    s = s.replace('0', '1')

    p = int((len(s) // 2))
    n = int(s[:p + 1])
    m = int(s[p:])

    i = m - n;
    if i < 0:
        i = -i
    s = i
 
    i = m - n
    if i < 0:
        i = -i;
    s += i;
    s *= 2;
    s = str(s);

    rate = (_size // 2) + 2

    res = ""
    for i in range(p+1):
        for x in range(1,5):
            num = int(d[i+x]) + int(s[i])
            if num >= rate:
                num -= rate
            res += str(num)

    return res
