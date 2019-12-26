# -*- coding: utf-8 -*-
import _pickle as cPickle
import logging
import struct
from socketserver import StreamRequestHandler, ThreadingTCPServer

from utils import RequestParser, EsHelper, GeoIpHelper

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8888
ES_HOST = 'localhost'
ES_PORT = 9200
ES_INDEX = 'wowhoneypot'
ES_TYPE = 'wowhoneypot'
# if enable GeoIP, set path to GeoLite2-City.mmdb
GEOIP_PATH = 'GeoLite2-City.mmdb'


class SocketLogHandler(StreamRequestHandler):
    def handle(self):
        print("connect from:", self.client_address)
        alldata = ""
        while True:
            chunk = self.request.recv(4)
            if len(chunk) < 4:
                break

            slen = struct.unpack(">L", chunk)[0]
            chunk = self.request.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.request.recv(slen - len(chunk))

            obj = cPickle.loads(chunk)
            record = logging.makeLogRecord(obj)
            message = record.getMessage()

            payload = RequestParser().tcp(message)
            payload['pot_ip'] = self.client_address[0]

            if GEOIP_PATH:
                try:
                    payload['client_geoip'] = GeoIpHelper(GEOIP_PATH).get(payload['client_ip'])
                except Exception as e:
                    print('Cannot get GeoIP {} {}'.format(payload['client_ip'], e))
            EsHelper(ES_HOST, ES_PORT, ES_INDEX, ES_TYPE).send(payload)
        self.request.close()


if __name__ == '__main__':
    server = ThreadingTCPServer((SERVER_HOST, SERVER_PORT), SocketLogHandler)
    print('listening:', server.socket.getsockname())
    server.serve_forever()
