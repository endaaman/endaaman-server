import asyncio
import argparse
import json
import logging
import logging.handlers
import os
import subprocess as sp

import http.server
from http import HTTPStatus
from urllib.parse import urlparse
from urllib.parse import parse_qs


fmt = '[%(asctime)s]%(levelname)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=fmt, datefmt='%Y-%m-%d %H:%M:%S',)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8080)
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--script', type=str, required=True)
args = parser.parse_args()

HOST = args.host
PORT = args.port
SCRIPT = os.path.abspath(args.script)

loop = asyncio.get_event_loop()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.log_client()
        self.respond(501)

    def do_POST(self):
        self.log_client()
        self.log_message(f'Starting {SCRIPT}')
        result = sp.Popen(['bash', SCRIPT]).wait()
        if result == 0:
            self.log_message(f'Done script.')
            status = 200
        else:
            self.log_error(f'Script failed.')
            status = 500
        self.respond(status)

    def respond(self, status):
        self.send_response(status)
        self.send_header('Content-length', 0)
        self.end_headers()

    def log_client(self):
        host, port = self.client_address
        self.log_message(f'{self.requestline} from {host}:{port}')

    def log_request(self, code='-', size='-'):
        return

    def log_message(self, fmt, *args):
        logger.info(fmt % args)

    def log_error(self, fmt, *args):
        logger.error(fmt % args)

if __name__ == '__main__':
    if not os.path.exists(SCRIPT):
        logger.error(f'Target script ({SCRIPT}) does not exist.')
        exit(1)

    httpd = http.server.HTTPServer((HOST, PORT), Handler)
    logger.info(f'Starting server at {HOST}:{PORT}')
    logger.info(f'Target script: {SCRIPT}')
    httpd.serve_forever()
    logger.info(f'Server closed.')
