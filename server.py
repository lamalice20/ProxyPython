import http.server as server
import socketserver as socket
import os
import json


def load_config(filename: str):
    with open(filename, "r") as f:
        return json.load(f)

data = load_config("conf/ipconfig.json")

handler = server.SimpleHTTPRequestHandler

os.chdir(data["path"])

httpd = socket.TCPServer((data["host"], data["port"]), handler)

try:
    print(f"Serveur lancée \nurl: http://{data["host"]}:{data["port"]}/\nVersion: {data["version"]}")
    httpd.serve_forever()
except KeyboardInterrupt:
    print("Serveur arrêté")
    httpd.shutdown()
    quit()