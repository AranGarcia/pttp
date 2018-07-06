#!/usr/bin/env python3
'''
Basic HTTP server

usage: pyserver [-h] [-p, --port PORT] [-w, --vhost DIR]

Simple python server that responds to GET and POST methods

optional arguments:
  -h, --help       show this help message and exit
  -p, --port PORT  listening server PORT number.
  -w, --vhost DIR  directory of the virtual host.

'''

import argparse
import os
import socket
import threading

import pttp

MAXLEN = 8192

class Server:
    '''
    HTTP server class that can respond to GET and POST messages.
    Default listening port is 8080.
    '''

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
        Start listening on the specified host and port.
        '''
        print('Serving HTTP at port', self.__port)
        print('Virtual host:', self.__vhost, '\n')

        pttp.VHOST = self.__vhost
        self.sock.listen(1)
        while True:
            conn, addr = self.sock.accept()
            print('REQUEST RECEVIED:', addr)

            # Read and parse the request
            message = bytearray()

            message += conn.recv(1024)
            while message[-4:] != pttp.END:
                message += conn.recv(1024)

                # Truncate request if it is too large
                if len(message) >= MAXLEN:
                    break
            # Manage request and create response
            stat, request = pttp.parsehttp(message)
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
        default='80',
        help='listening server PORT number.',
        metavar='PORT',
        type=int
    )
    parser.add_argument(
        '-w, --vhost',
        dest='vhost',
        default='./src/html/',
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
