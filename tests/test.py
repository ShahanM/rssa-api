"""
test.py
"""
import requests
import json

with open('test_ratings.json') as f:
    data = json.load(f)

host = 'http://127.0.0.1:6000'
endpoint = 'preferences'
res = requests.post(f' {host}/{endpoint}', json=dict(ratings=data['ratings'], user_id=None))
print(res.text)