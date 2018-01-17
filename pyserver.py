#!/usr/bin/env python3
'''
Basic HTTP server

usage: server.py [-h] port

positional arguments:
  port        Listening server port number

optional arguments:
  -h, --help  show this help message and exit
'''

import argparse
import os
import socket

import pttp


class Server:
    '''
    HTTP server class that can respond to GET and POST messages.
    Default listening port is 8080.
    '''
    stance = None

    def __init__(self, **kwargs):
        self.__host = ''
        self.__port = kwargs['port']

        self.__vhost = os.path.abspath(kwargs['vhost'])

        # Socket binding
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.__host, self.__port))

    def start(self):
        '''
        Start listening on the specified host and port
        using blocking mode.
        '''
        print('pHTTP')
        print('Serving HTTP at port', self.__port)
        print('Virtual host:', self.__vhost)
        print()
        self.sock.listen(1)
        while True:
            conn, addr = self.sock.accept()
            print('Request receieved:', addr)

            # Read and parse the request
            END = b'\r\n\r\n'
            message = bytearray()

            message += conn.recv(1024)
            while message[-4:] != END:
                message += conn.recv(1024)

            pttp.parseHTTP(message)

            # Manage request
            stat, request = pttp.parseHTTP(message)
            print(request)
            response = pttp.HTTPresponse(request, stat)
            print(response, '\n')

            conn.sendall(bytes(response))
            conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='pyserver',
        description='Simple python server that responds to GET and POST methods'
    )

    # Arguments
    parser.add_argument(
        '-p, --port',
        dest='port',
        default='8080',
        help='listening server PORT number.',
        metavar='PORT',
        type=int
    )
    parser.add_argument(
        '-w, --vhost',
        dest='vhost',
        default='.',
        help='directory of the virtual host.',
        metavar='DIR'
    )

    args = parser.parse_args()
    kw = vars(args)

    s = Server(**kw)
    try:
        s.start()
    except KeyboardInterrupt:
        print('\rServer terminated.')
