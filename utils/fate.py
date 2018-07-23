#!/usr/bin/env python3
# fate.py
# This script determines the most favorable currencies to purchase Fate in.
# Due to StoryNexus response times, execution times can take up to one minute.
# Prerequisites: Fallen London account, fixer.io account
# Requirements: requests, beautifulsoup4

from bs4 import BeautifulSoup as Soup
import netrc
from operator import itemgetter
import re
import requests

target_currency = 'USD'

creds = netrc.netrc()
fl = creds.authenticators('fallenlondon')
fixer = creds.authenticators('fixer.io')

s = requests.Session()
data = {'emailAddress': fl[0], 'password': fl[2]}
r = s.post('http://fallenlondon.storynexus.com/Auth/EmailLogin', data=data)
r = s.get('http://fallenlondon.storynexus.com/sn/BuyNexBraintree')

soup = Soup(r.text, 'lxml')
select = soup.find('select', id='currency-code')
currencies = [option.text for option in select.children]

if target_currency not in currencies:
    params={'access_key': fixer[0],
            'symbols': ','.join(currencies + [target_currency])}
else:
    params={'access_key': fixer[0],
            'symbols': ','.join(currencies)}
r = requests.get('http://data.fixer.io/api/latest', params=params).json()
rates = {k: 1 / r['rates'][target_currency] * v for k, v in r['rates'].items()}

fate_rates = []
for currency in currencies:
    page = s.get('https://fallenlondon.storynexus.com/sn/BuyNexBraintree?currencyCode={}'.format(currency))
    soup = Soup(page.text, 'lxml')
    nums = soup.find('ul')
    cur_rates = [tag.text.strip() for tag in nums.children if not isinstance(tag, str)]
    for rate in cur_rates:
        m = re.match(r'^(\d+) FATE .+?([\d\.]+)$', rate)
        fate = int(m.group(1))
        cost = float(m.group(2))
        fate_rates.append((currency, fate, cost, fate/cost * rates[currency]))
fate_rates.sort(key=itemgetter(3), reverse=True)

print('The most favorable currencies (ignoring forex fees) are:')
for rate in fate_rates:
    if rate[0] in currencies:
        print('{rate[0]}: {rate[1]} for {rate[2]} {rate[0]} ({rate[3]:.3f} Fate per {0})'.format(target_currency, rate=rate))
        currencies.remove(rate[0])
