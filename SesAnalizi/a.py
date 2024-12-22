import requests

url = "http://127.0.0.1:5000/duygu-analizi"
response = requests.post(url, json={"metin": "Bugün çok mutluyum!"})
print(response.json())
