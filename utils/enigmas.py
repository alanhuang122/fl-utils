#!/usr/bin/env python3

from http.client import responses
from datetime import datetime
import requests
import json
import netrc
import sys

print('current time {}'.format(datetime.now()))
api = 'https://api.fallenlondon.com/api/{}'
login = netrc.netrc('/home/alan/.netrc').authenticators('fallenlondon')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}

s = requests.Session()
s.headers = headers

# auth
print('logging in..........................', end='')
r = s.post(api.format('login'), data={'email': login[0], 'password': login[2]})

if r.status_code != 200:
    sys.exit('login failed with code {} ({})'.format(r.status_code, responses[r.status_code]))

s.headers.update({'Authorization': 'Bearer {}'.format(r.json()['Jwt'])})
print('success.')

current_area = r.json()['Area']['Id']

print('getting actions.....................', end='')
r = s.get(api.format('character/sidebar'))

if r.status_code != 200:
    sys.exit('getting sidebar info failed with code {} ({})'.format(r.status_code, responses[r.status_code]))

actions = r.json()['Actions']
print('{} action{} available'.format(actions, '' if actions == 1 else 's'))

print('getting storylet info...............', end='')
r = s.post(api.format('storylet'))

if r.status_code != 200:
    sys.exit('getting storylet info failed with code {} ({})'.format(r.status_code, responses[r.status_code]))
print('success.')

state = r.json()
if state['Phase'] == 'In' and state['Storylet']['Id'] != 284781: # title: Court of the Wakeful Eye
    sys.exit('You are not in the right storylet.')

# should be in the storylet
storylet = r.json()['Storylet']
branches = storylet['ChildBranches']

failures = 0
while actions > 3:
    for branch in branches:
        if branch['Id'] == 211145:
            if branch['IsLocked']:
                sys.exit('done (branch is locked)')
                break
    
    r = s.post(api.format('storylet/choosebranch'), data={'branchId': 211145, 'secondChanceIds': []})
    if r.status_code != 200:
        failures += 1
        print('action failed with code {} ({})'.format(r.status_code, responses[r.status_code]))
    else:
        failures = 0
        try:
            end = r.json()['EndStorylet']
            actions = end['CurrentActionsRemaining']
            for message in r.json()['Messages']['DefaultMessages']:
                print(message['Message'])
            print('{} actions remaining...\n'.format(actions))
        except TypeError:
            pass
        r = s.post(api.format('storylet'))
        while r.status_code != 200 and failures < 3:
            failures += 1
            print('resolution failed with code {} ({})'.format(r.status_code, responses[r.status_code]))
            r = s.post(api.format('storylet'))
    if failures >= 3:
        sys.exit('done (3 consecutive failures)')

print('done (success)')
