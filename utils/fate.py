#!/usr/bin/env python3
# fate.py
# This script determines the most favorable currencies to purchase Fate in.
# Due to StoryNexus response times, execution times can take up to one minute.
# Prerequisites: Fallen London account, fixer.io account
# Requirements: requests

import netrc
from operator import itemgetter
import re
import requests

s = requests.Session()
api = 'https://api.fallenlondon.com/api/{}'
target_currency = 'USD'

# Authenticate with FL
creds = netrc.netrc()
fl = creds.authenticators('fallenlondon')
data = {'email': fl[0], 'password': fl[2]}
r = s.post(api.format('login'), data=data)
s.headers.update({'Authorization': f'Bearer {r.json()["jwt"]}'})

# Get Fate purchase info
r = s.get(api.format(f'nex/braintreenexoptions/USD')).json()
currencies = r['currencies']
offerings = r['packages']
currency_list = [i['code'] for i in currencies.values()]

# Get exchange rate data
fixer = creds.authenticators('fixer.io')
if target_currency not in currency_list:
    params={'access_key': fixer[0],
            'symbols': ','.join(currency_list + [target_currency])}
else:
    params={'access_key': fixer[0],
            'symbols': ','.join(currency_list)}

r = requests.get('http://data.fixer.io/api/latest', params=params).json()
rates = {k: 1 / r['rates'][target_currency] * v for k, v in r['rates'].items()}

# Calculate Fate rates
fate_rates = []
for currency in currency_list:
    for offering in offerings:
        fate = offering['quantity']
        cost = currencies[currency.lower()]['dollarValue'] * offering['dollarPrice']
        fate_rates.append((currency, fate, cost, fate/cost * rates[currency]))

fate_rates.sort(key=itemgetter(3), reverse=True)

# List best exchange rate per currency
print('The most favorable currencies (ignoring forex fees) are:')
for rate in fate_rates:
    if rate[0] in currency_list:
        print('{rate[0]}: {rate[1]} for {rate[2]:.2f} {rate[0]} ({rate[3]:.3f} Fate per {0})'.format(target_currency, rate=rate))
        currency_list.remove(rate[0])
