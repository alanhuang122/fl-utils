#!/usr/bin/python2
from Crypto.Cipher import AES
from base64 import b64decode
import json, requests
import os,errno
from requests_toolbelt import MultipartDecoder as Decoder
from datadiff import diff

last_seq = 0
data = {}
changes = {}
old = {}

def decrypt(text):
    key = 'eyJUaXRsZSI6Ildo'
    iv = '\0' * 16

    cbc = AES.new(key, AES.MODE_CBC, iv)
    plain_text = cbc.decrypt(b64decode(text)).decode('utf-8')

    # Remove PKCS#7 padding
    return plain_text[:-ord(plain_text[-1])]

def get(id, revision):
    data = requests.get('http://couchbase-fallenlondon.storynexus.com:4984/sync_gateway_json/{}?rev={}&revs=true&attachments=true'.format(id, revision), headers={'Host': 'couchbase-fallenlondon.storynexus.com:4984', 'User-Agent': None, 'Accept-Encoding': None, 'Connection': None}).json()
    return decrypt(data['body'])

def acquire(id, revision):
    print(('acquiring {}'.format(id)))
    return json.loads(get(id, revision))

def acquire_bulk(changes):
    postlist = []
    for change in changes:
        postlist.append('{{"id":"{}","rev":"{}","atts_since":[]}}'.format(change['id'], change['changes'][0]['rev']))
    payload = '{{"docs":[{}]}}'.format(','.join(postlist))
    post_headers={"Host": 'couchbase-fallenlondon.storynexus.com:4984', "Content-Type": "application/json", "Connection": None, "Accept-Encoding": None, "Accept": None, "User-Agent": None}
    r = requests.post('http://couchbase-fallenlondon.storynexus.com:4984/sync_gateway_json/_bulk_get?revs=true&attachments=true', data=payload, headers=post_headers)
    decoder = Decoder.from_response(r)
    updates = [json.loads(x.text) for x in decoder.parts]
    dec = []
    for u in updates:
        try:
            dec.append(json.loads(decrypt(u['body'])))
        except KeyError:
            print(u)
    return dec

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
    try:
        os.makedirs('text')
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    with open('./text/fl.dat', 'w+') as f:
        f.write('{}\n'.format(last_seq))
        for i in list(data.items()):
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
    if len(list(revisions.values())) == 1:
        updates = [acquire(list(revisions.values())[0]['id'], list(revisions.values())[0]['changes'][0]['rev'])]
    elif len(list(revisions.values())) > 1 and len(list(revisions.values())) < 50:
        updates = acquire_bulk(list(revisions.values()))
    else:
        print(('getting {} records...'.format(len(list(revisions.values())))))
        updates = []
        chunks = [list(revisions.values())[i:i+50] for i in range(0, len(list(revisions.values())), 50)]
        for chunk in chunks:
            updates += acquire_bulk(chunk)
    for item in zip([x['id'] for x in list(revisions.values())], updates):
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
    print(diff(old[key], data[key]))

def pe():
    for x in changes['events']:
        print(x, data['events:{}'.format(x)].get('Name'))

def pq():
    for x in changes['qualities']:
        print(x, data['qualities:{}'.format(x)].get('Name'))

load()
import fl
fl.data=data
update()
save()
