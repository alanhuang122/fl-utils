#!/usr/bin/python2
from Crypto.Cipher import AES
from base64 import b64decode
import json, requests
from requests_toolbelt import MultipartDecoder as Decoder
from datadiff import diff

last_seq = 0
data = {}
changes = {}
old = {}

def first(text,key):
    ecb = AES.new(key, AES.MODE_ECB)
    return ecb.decrypt(b64decode(text))[:16]
    
def second(text,key,iv):
    ecb = AES.new(key, AES.MODE_CBC, iv)
    return ecb.decrypt(b64decode(text))[16:].replace('\x0c','')
    
def decrypt(text):
    key = 'eyJUaXRsZSI6Ildo'
    iv = b64decode('7ENDyFzB5uxEtjFCpRpj3Q==')
    return first(text,key)+second(text,key,iv)

def get(id, revision):
    data = requests.get('http://couchbase-fallenlondon.storynexus.com:4984/sync_gateway_json/{}?rev={}&revs=true&attachments=true'.format(id, revision), headers={'Host': 'couchbase-fallenlondon.storynexus.com:4984', 'User-Agent': None, 'Accept-Encoding': None, 'Connection': None}).json()
    return decrypt(data['body'])

def clean(s):
    temp = s.rsplit('}', 1)
    return '{}}}'.format(temp[0])

def acquire(id, revision):
    print('acquiring {}'.format(id))
    return json.loads(unicode(clean(get(id, revision)), 'utf-8'))

def acquire_bulk(changes):
    postlist = []
    for change in changes:
        postlist.append('{{"id":"{}","rev":"{}","atts_since":[]}}'.format(change['id'], change['changes'][0]['rev']))
    payload = '{{"docs":[{}]}}'.format(','.join(postlist))
    post_headers={"Host": 'couchbase-fallenlondon.storynexus.com:4984', "Content-Type": "application/json", "Connection": None, "Accept-Encoding": None, "Accept": None, "User-Agent": None}
    r = requests.post('http://couchbase-fallenlondon.storynexus.com:4984/sync_gateway_json/_bulk_get?revs=true&attachments=true', data=payload, headers=post_headers)
    decoder = Decoder.from_response(r)
    updates = [json.loads(x.text) for x in decoder.parts]
    return [json.loads(unicode(clean(decrypt(u['body'])), 'utf-8')) for u in updates]

def load():
    global data
    global last_seq
    print('loading...')
    try:
        with open('./text/fl.dat') as f:
            last_seq = int(f.readline())
            for line in f:
                temp = json.loads(line)
                data[temp['key']] = temp['value']
    except:
        pass

def save():
    with open('./text/fl.dat', 'w') as f:
        f.write('{}\n'.format(last_seq))
        for i in data.items():
            json.dump({'key': i[0], 'value': i[1]}, f)
            f.write('\n')

from collections import OrderedDict

def update():
    global last_seq
    revisions = OrderedDict()
    headers = {"Host": 'couchbase-fallenlondon.storynexus.com:4984', "Content-Type": "application/json", "Connection": None, "Accept-Encoding": None, "Accept": None, "User-Agent": None}
    payload = '{{"feed":"longpoll","heartbeat":300000,"style":"all_docs","since":{},"limit":500}}'
    print('getting updates...')
    while True:
        try:
            r = requests.post('http://couchbase-fallenlondon.storynexus.com:4984/sync_gateway_json/_changes', data=payload.format(last_seq), headers=headers, timeout=1)
            response = r.json()
            for row in response['results']:
                if row['seq'] < 6000:
                    continue
                revisions[row['id']] = row
            last_seq = response['last_seq']
        except:
            break
    if not revisions:
        print('no updates')
        return
    if len(revisions.values()) == 1:
        updates = [acquire(revisions.values()[0]['id'], revisions.values()[0]['changes'][0]['rev'])]
    elif len(revisions.values()) > 1 and len(revisions.values()) < 50:
        updates = acquire_bulk(revisions.values())
    else:
        print('getting {} records...'.format(len(revisions.values())))
        updates = []
        chunks = [revisions.values()[i:i+50] for i in xrange(0, len(revisions.values()), 50)]
        for chunk in chunks:
            updates += acquire_bulk(chunk)
    for item in zip([x['id'] for x in revisions.values()], updates):
        if item[0] in data:
            old[item[0]] = data[item[0]]
            print('updated key: {}'.format(item[0]))
        else:
            print('new key: {}'.format(item[0]))
        data[item[0]] = item[1]
        datatype, id = item[0].split(':')
        id = int(id)
        try:
            changes[datatype].append(id)
        except KeyError:
            changes[datatype] = [id]
    
def print_diff(key):
    print(str(diff(old[key], data[key])).decode('string-escape'))

load()
import fl
fl.data=data
update()
save()
