#!/usr/bin/python3
from Crypto.Cipher import AES
from base64 import b64decode
import json, requests
from requests_toolbelt import MultipartDecoder as Decoder
from datadiff import diff
from collections import OrderedDict

last_seq = 0
data = {}
changes = {}
old = {}

def first(text,key):
    ecb = AES.new(key, AES.MODE_ECB)
    return ecb.decrypt(b64decode(text))[:16]
    
def second(text,key,iv):
    ecb = AES.new(key, AES.MODE_CBC, iv)
    return ecb.decrypt(b64decode(text))[16:].replace(b'\x0c',b'')
    
def decrypt(text):
    key = 'eyJUaXRsZSI6Ildo'
    iv = b64decode('7ENDyFzB5uxEtjFCpRpj3Q==')
    return first(text,key)+second(text,key,iv)

def get(id, revision):
    data = requests.get('http://couchbase-fallenlondon.storynexus.com:4984/sync_gateway_json/{}?rev={}&revs=true&attachments=true'.format(id, revision), headers={'Host': 'couchbase-fallenlondon.storynexus.com:4984', 'User-Agent': None, 'Accept-Encoding': None, 'Connection': None}).json()
    return decrypt(data['body'].encode('utf-8'))

def clean(s):
    temp = s.rsplit(b'}', 1)
    return temp[0] + b'}'

def acquire(id, revision):
    print(('acquiring {}'.format(id)))
    return json.loads(str(clean(get(id, revision))))

def acquire_bulk(changes):
    postlist = []
    for change in changes:
        postlist.append('{{"id":"{}","rev":"{}","atts_since":[]}}'.format(change['id'], change['changes'][0]['rev']))
    payload = '{{"docs":[{}]}}'.format(','.join(postlist))
    post_headers={"Host": 'couchbase-fallenlondon.storynexus.com:4984', "Content-Type": "application/json", "Connection": None, "Accept-Encoding": None, "Accept": None, "User-Agent": None}
    r = requests.post('http://couchbase-fallenlondon.storynexus.com:4984/sync_gateway_json/_bulk_get?revs=true&attachments=true', data=payload, headers=post_headers)
    decoder = Decoder.from_response(r)
    updates = [json.loads(x.text) for x in decoder.parts]
    return [json.loads(clean(decrypt(u['body']))) for u in updates]

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
        for i in list(data.items()):
            json.dump({'key': i[0], 'value': i[1]}, f)
            f.write('\n')

def update():
    global last_seq
    revisions = []
    headers = {"Host": 'couchbase-fallenlondon.storynexus.com:4984', "Content-Type": "application/json", "Connection": None, "Accept-Encoding": None, "Accept": None, "User-Agent": None}
    payload = '{{"feed":"longpoll","heartbeat":300000,"style":"all_docs","since":{},"limit":500}}'
    while True:
        try:
            r = requests.post('http://couchbase-fallenlondon.storynexus.com:4984/sync_gateway_json/_changes', data=payload.format(last_seq), headers=headers, timeout=1)
            response = r.json()
            for row in response['results']:
                if row['seq'] < 6000:
                    continue
                revisions.append(row)
            last_seq = response['last_seq']
        except:
            break
    if not revisions:
        print('no updates')
        return
    if len(revisions) == 1:
        updates = [acquire(revisions[0]['id'], revisions[0]['changes'][0]['rev'])]
    elif len(revisions) > 1 and len(revisions) < 50:
        updates = acquire_bulk(revisions)
    else:
        print(('getting {} records...'.format(len(revisions))))
        updates = []
        chunks = [revisions[i:i+50] for i in range(0, len(revisions), 50)]
        for chunk in chunks:
            updates += acquire_bulk(chunk)
    for item in zip([x['id'] for x in revisions], updates):
        if item[0] in data:
            old[item[0]] = data[item[0]]
            print(('updated key: {}'.format(item[0])))
        else:
            print(('new key: {}'.format(item[0])))
        data[item[0]] = item[1]
        datatype, id = item[0].split(':')
        id = int(id)
        try:
            changes[datatype].append(id)
        except KeyError:
            changes[datatype] = [id]
   
def print_diff(key):
    print(bytes(str(diff(old[key], data[key])), 'utf-8').decode('unicode_escape'))

load()
update()
import fl
fl.data=data
save()
