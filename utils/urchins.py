#!/usr/bin/env python

from http.client import responses
import datetime
import requests
import json
import netrc
import sys

print('current time {}'.format(datetime.now()))
api = 'https://api.fallenlondon.com/api/{}'
login = netrc.netrc().authenticators('fallenlondon')

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

r = s.post(api.format('storylet'))

if r.status_code != 200:
    sys.exit('getting storylet info failed with code {} ({})'.format(r.status_code, responses[r.status_code]))

state = r.json()
if state['Phase'] == 'In' and state['Storylet']['Id'] != 285304: # title: Offering Tribute to the Court of the Wakeful Eye
    print('in different storylet, going back...')
    if not state['Storylet']['CanGoBack']:
        sys.exit('You are in storylet {}, and cannot go back.'.format(state['Storylet']['Name']))
    else:
        r = s.post(api.format('storylet/goback'))
        if r.status_code != 200:
            sys.exit('going back failed with code {} ({})'.format(r.status_code, responses[r.status_code]))
        state = r.json()
    print('success.')


if state['Phase'] == 'Available':
    if current_area != 28:
        print('moving to labyrinth of tigers.......', end='')
        r = s.get(api.format('map'))
        if r.status_code != 200:
            sys.exit('getting map failed with code {} ({})'.format(r.status_code, responses[r.status_code]))

        index = -1
        areas = r.json()['Areas']
        for area in areas:
            if area['Id'] == 28: # The Labyrinth of Tigers
                r = s.post(api.format('map/move/28'))
                if r.status_code != 200 or not r.json()['IsSuccess']:
                    sys.exit('moving failed\ndata: {}'.format(r.text))

    print('success.')
    r = s.post(api.format('storylet'))

    if r.status_code != 200:
        sys.exit('getting storylet info failed with code {} ({})'.format(r.status_code, responses[r.status_code]))

    print('entering storylet...................', end='')
    storylets = r.json()['Storylets']

    for storylet in storylets:
        if storylet['Id'] == 285304:
            r = s.post(api.format('storylet/begin/285304'))
            if r.status_code != 200 or not r.json()['IsSuccess']:
                sys.exit('failed to start storylet\ndata: {}'.format(r.text))
    print('success.')


# should be in the storylet
storylet = r.json()['Storylet']
branches = storylet['ChildBranches']

failures = 0
while actions > 0:
    for branch in branches:
        if branch['Id'] == 211014:
            if branch['IsLocked']:
                sys.exit('done (branch is locked)')
            break
    
    r = s.post(api.format('storylet/choosebranch'), data={'branchId': 211014, 'secondChanceIds': []})
    if r.status_code != 200:
        failures += 1
        print('action failed with code {} ({})'.format(r.status_code, responses[r.status_code]))
    else:
        failures = 0
        end = r.json()['EndStorylet']
        actions = end['CurrentActionsRemaining']
        for message in r.json()['Messages']['DefaultMessages']:
            print(message['Message'])
        print('{} actions remaining...\n'.format(actions))
    if failures >= 3:
        sys.exit('done (3 consecutive failures)')

print('done (success)')
