from bs4 import BeautifulSoup,Tag,NavigableString
from bs4.element import Comment
from bs4.element import PageElement
from itertools import takewhile
import json
import decimal
from google.cloud import translate_v2 as translate
import re
from collections import deque

phrasingcon = ['abbr','audio','b','bdi','bdo','br','button','canvas','cite','code',
                   'data','datalist','dfn','em','embed','i','iframe','img','input','kbd',
                   'label','mark','math','meter','noscript','object','output','picture',
                   'progress','q','ruby','s','samp','script','select','slot','small','span',
                   'strong','sub','sup','svg','template','textarea','time','u','var','video','wbr','a',None]

def chunk(array : list, num : int) -> list[list]:
    length = len(array)
    ret = []
    for i in range(0,length,num):
        ret.append(array[i:i+num])
    return ret

def translate_text(text_list : list[str], client : translate.Client ) -> list[str]:
    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    ret = []
    for arr in chunk(text_list, 20):
        try:
            ret += [result["translatedText"] for result in client.translate(arr, target_language="en")]
        except Exception as inst:
            print(arr)
            
    
    return ret

def ischinese(s : str):
    return bool(re.search(u'[\u4e00-\u9fff]',s))

def lstripped(s):
    return ''.join(takewhile(str.isspace, s))

def rstripped(s):
    return ''.join(reversed(tuple(takewhile(str.isspace, reversed(s)))))

def all_phrase(element : Tag):
    for x in element.descendants:
        if x.name not in phrasingcon:
            return False
    return True

def check(element : Tag):
    if element.parent == None:
        return False
    if element.name in ['style', 'script', 'head', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    if element.parent in phrasingcon:
        return False
    par_all = all_phrase(element.parent)
    ele_all = all_phrase(element)
    if element.name in phrasingcon and not par_all and ele_all:
        return ischinese(str(element))
    if element.name in phrasingcon and par_all:
        return False
    return ele_all and ischinese(str(element))

def translate_html(html_doc : str, client : translate.Client) -> str:
    soup = BeautifulSoup(html_doc, 'html.parser')
    if soup.html:
        soup.html["lang"] = "en"
    p : list[Tag] = list(filter(lambda x : check(x), soup.find_all()))
    to_trans = [str(i) for i in p]
    trans = translate_text(to_trans, client)
    for elem, string in zip(p,trans):
        phrase = BeautifulSoup(string,'html.parser')
        elem.replace_with(phrase)
    return str(soup)

def get_json(json_obj, q : deque):
    if type(json_obj) is list:
        for x in json_obj:
            get_json(x,q)
    elif type(json_obj) is dict:
        for v in json_obj.values():
            get_json(v,q)
    elif type(json_obj) is str and ischinese(json_obj):
        q.appendleft(json_obj)

def put_json(json_obj, q : deque) -> None | str:
    if type(json_obj) is list:
        for i,v in enumerate(json_obj):
            val = put_json(v,q)
            if val:
                json_obj[i] = val
    elif type(json_obj) is dict:
        for k,v in json_obj.items():
            val = put_json(v,q)
            if val:
                json_obj[k] = val
    elif type(json_obj) is str and ischinese(json_obj):
        return q.pop()


def translate_json(json_doc : str, client : translate.Client) -> str:
    loaded = json.loads(json_doc, parse_float=decimal.Decimal)
    q = deque()
    get_json(loaded,q)
    to_trans = list(q)
    trans = translate_text(to_trans, client)
    put_json(loaded, deque(trans))
    return json.dumps(loaded)