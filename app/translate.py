import json
import requests
from flask_babel import _


def translate(text, source_language, dest_language):
    r = requests.get('https://api.mymemory.translated.net/get?q=%s&langpair=%s|%s' %(text, source_language, dest_language))
    if r.status_code != 200:
        return _('Error: the translation service failed.')
    return json.loads(r.content.decode('utf-8-sig'))['responseData']['translatedText']
