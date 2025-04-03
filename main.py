from functools import lru_cache
from urllib.parse import urlparse
import socketserver
import http.server
import requests
import socket
import select
import logging
import argparse
import json

# Configuration du logger avec enregistrement uniquement dans un fichier
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("proxy.log", encoding="utf-8")  # Enregistre uniquement dans proxy.log
    ]
)

logger = logging.getLogger(__name__)  # Création du logger

@lru_cache(maxsize=10000)
class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        target_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        logger.info(f"Requête GET reçue pour: {target_url}")
        
        try:
            response = requests.get(target_url, headers=self.headers, stream=True)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in ['transfer-encoding', 'content-encoding']:
                    self.send_header(key, value)
            self.end_headers()
            
            for chunk in response.iter_content(4096):
                self.wfile.write(chunk)
        except requests.RequestException as e:
            logger.error(f"Erreur de connexion au serveur distant: {e}")
            self.send_error(502, f"Erreur de connexion au serveur distant: {e}")

    def do_CONNECT(self):
        host, port = self.path.split(":")
        port = int(port)
        
        logger.info(f"Requête CONNECT reçue pour: {host}:{port}")
        
        try:
            with socket.create_connection((host, port)) as remote_socket:
                self.send_response(200, "Connection established")
                self.end_headers()
                
                client_socket = self.connection
                
                sockets = [client_socket, remote_socket]
                while True:
                    readable, _, _ = select.select(sockets, [], [])
                    for sock in readable:
                        data = sock.recv(4096)
                        if not data:
                            return
                        sock_pair = remote_socket if sock is client_socket else client_socket
                        sock_pair.sendall(data)
        except Exception as e:
            logger.error(f"Erreur lors de l'établissement du tunnel: {e}")
            self.send_error(502, f"Erreur lors de l'établissement du tunnel: {e}")
    
    

@lru_cache(maxsize=10000)
class ThreadedProxyServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass


parser = argparse.ArgumentParser()

parser.add_argument("--empty", action="store_true", help="Vide le fichier de log")
parser.add_argument("--clearcache", action="store_true", help="Vide le cache du script pour déchargé votre ram")
parser.add_argument("--start", action="store_true", help="démarre le proxy")

arg = parser.parse_args()

if arg.empty:
    with open("proxy.log", "w+")as f:
        print(f"Fichier log vidé !")
        f.write("")
    
if arg.clearcache:
    ProxyHandler.cache_clear()
    print(f"cache vider pour ProxyHandler...")

    ThreadedProxyServer.cache_clear()
    print(f"cache vider pour ThreadedProxyServer...")

    print("Caches vidé !")

if arg.start:
    with open("config.json", "r") as f:
        data = json.load(f)

    HOST, PORT = str(data["host"]), int(data["port"])
    logger.info(f"Démarrage du serveur proxy sur {HOST}:{PORT}")
    with ThreadedProxyServer((HOST, PORT), ProxyHandler) as server:
        server.serve_forever()
