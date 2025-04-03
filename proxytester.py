import requests as re

proxy = {
    "https" : "http://127.0.0.1:8080",
    "http" : "http://127.0.0.1:8080" 
}

while True:
    response = re.get("https://google.com/", proxies=proxy)

    print(response.text)