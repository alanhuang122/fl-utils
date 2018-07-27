#!/usr/bin/python
import json

last_seq = 0
data = {}

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

load()
import fl
fl.data=data
