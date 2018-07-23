from bs4 import BeautifulSoup as Soup
import netrc
from operator import itemgetter
import re
import requests

creds = netrc.netrc()

fl = creds.authenticators('fallenlondon')
fixer = creds.authenticators('fixer.io')

s = requests.Session()

r = s.post('http://fallenlondon.storynexus.com/Auth/EmailLogin', data={'emailAddress': fl[0], 'password': fl[2]})
r = s.get('http://fallenlondon.storynexus.com/sn/BuyNexBraintree')

soup = Soup(r.text, 'lxml')

select = soup.find('select', id='currency-code')
currencies = [option.text for option in select.children]
target_currency = 'USD'
if target_currency not in currencies:
    r = requests.get('http://data.fixer.io/api/latest', params={'access_key': fixer[0], 'symbols': ','.join(currencies + [target_currency])}).json()
else:
    r = requests.get('http://data.fixer.io/api/latest', params={'access_key': fixer[0], 'symbols': ','.join(currencies)}).json()
rates = {k: 1 / r['rates'][target_currency] * v for k, v in r['rates'].items()}

fate_rates = []

for currency in currencies:
    page = s.get(f'https://fallenlondon.storynexus.com/sn/BuyNexBraintree?currencyCode={currency}')
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
        print(f'{rate[0]}: {rate[1]} for {rate[2]} {rate[0]} ({rate[3]:.3f} Fate per {target_currency})')
        currencies.remove(rate[0])
