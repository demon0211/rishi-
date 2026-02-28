import requests

url = 'http://127.0.0.1:5000/process'
files = {'file': ('test.txt', 'This is a test.')}
data = {'template': 'ieee', 'format': 'pdf'}
try:
    resp = requests.post(url, files=files, data=data)
    print("Status:", resp.status_code)
    print("Body:", resp.text)
except Exception as e:
    print("Error:", e)
