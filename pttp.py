'''
Implementations for HTTP parsing request and building responses
'''

import os
import re

METHODS = (b'GET', b'HEAD', b'POST', b'OPTIONS')
END = b'\r\n\r\n'
VHOST = b'./'


class HTTPmessage:
    '''
    Generalization of attributes shared in HTTP requests and responses, such as headers.
    '''

    def __init__(self, version=b'HTTP/1.1', headers=None, body=b''):
        self.version = version
        if headers is None:
            self.headers = {}
        else:
            self.headers = headers
        self.body = body


class HTTPrequest(HTTPmessage):
    '''
    Class implementation of a HTTP request as established in the RFC 7230
    [https://www.rfc-editor.org/rfc/rfc7230.txt]
    '''

    def __init__(self, method, target, version, headers, body=None):
        super(HTTPrequest, self).__init__(version, headers, body)
        self.method = method

        self.parameters = {}
        self.__parsetarget(target)

    def __parsetarget(self, target):
        try:
            pos = target.index(b'?')
            self.target = target[:pos]

            qstring = target[pos + 1:]

            for part in qstring.split(b'&'):
                q, p = part.split(b'=')
                self.parameters[q.decode()] = p.decode()

        except ValueError:
            self.target = target

    def __str__(self):
        # Do the closest thing as a string builder, so if there are any headers they should
        # all be printed out
        headers_text = bytearray()

        for k, v in self.headers.items():
            line = b'\t' + k + b' : ' + v + b'\n'
            headers_text.extend(line)

        return '%s %s %s\n%s' % (
            self.method.decode(), self.target.decode(),
            self.version.decode(), headers_text.decode()
        )


class HTTPresponse(HTTPmessage):
    '''
    Class implementation of an HTTP response, as specified in the RFC 7230
    [https://www.rfc-editor.org/rfc/rfc7230.txt]
    '''

    def __init__(self, httpreq=None, statcode=0):
        super(HTTPresponse, self).__init__()
        if httpreq is None:
            print('There was an error')
            self.status = statcode
            self.stattext = HTTPerror.getstattext(statcode)
            self.body = HTTPerror.getbody(statcode)

        # Status line
        self.status = None
        self.stattext = None

        self.__buildresponse(httpreq)

    def __buildresponse(self, request):
        # Status line
        self.status = 200
        self.stattext = b'OK'

        # Check for 404
        try:
            # Body
            if request.target == b'/':
                index = HTTPresponse.__find_index()

                print("index is ",index)
                if not index:
                    raise FileNotFoundError

                target = VHOST.encode() + index
            else:
                target = request.target[1:]

            print("Opening file", target)
            with open(target.decode(), mode='rb') as tfile:
                self.body = tfile.read()
        except FileNotFoundError:
            self.status = 404
            self.__builderr(404)

    def __builderr(self, status):
        ''' TODO: Use the HTTPerror class  '''
        self.stattext = HTTPerror.getstattext(status)
        self.body = HTTPerror.getbody(status)

    def __bytes__(self):
        headerlist = [b'%s: %s' % (k, v) for k, v in self.headers.items()]
        return b'%s %s %s\n%s\n%s' % (
            self.version, str(self.status).encode(), self.stattext,
            b'\r\n'.join(headerlist), self.body
        )

    def __str__(self):
        return '%s %s %s' % (
            self.version.decode(), str(self.status), self.stattext.decode())

    @staticmethod
    def __find_index():
        files = os.listdir(VHOST)
        p = re.compile('index.((html)|(php))')

        for f in files:
            if p.match(f):
                return f.encode()
        
        return None


class HTTPerror:
    '''
    Definitcion of constants for HTTP statuses  and their
    respective reponse body
    '''
    stattext = {
        200: b'OK', 400: b'Bad Request', 404: b'Not Found',
        405: b'Method Not Allowed'
    }

    @classmethod
    def getbody(cls, status):
        ''' Gets the response body of a status code. '''
        fname = 'src/html/stat/' + str(status) + '.html'
        with open(fname, 'rb') as errfile:
            return errfile.read()

    @classmethod
    def getstattext(cls, status):
        ''' Gets the description of the status code for the response.'''
        return cls.stattext[status]


def parsehttp(message):
    '''
    Processing of an HTTP message according to section 3 of the
    RFC 7230, Message Format
    [https://tools.ietf.org/html/rfc7230#section-3]

    Returns the status code for the response and a request object.

    parsehttp(message) -> status_code, HTTPrequest
    '''
    print('Parsing')
    # Request Line
    start = 0
    end = message.find(b'\r\n')
    reqline = message[start:end]
    try:
        method, target, version = bytes(reqline).split(b' ')
    except ValueError:
        return None, 400

    # Headers
    start = end + 2
    end = message.find(b'\r\n', start)
    if start == end:
        return None, 400
    headers = {}
    line = message[start:end]
    while line:
        header, value = line.split(b':', 1)
        headers[bytes(header.strip())] = bytes(value.strip())

        start = end + 2
        end = message.find(b'\r\n', start)
        line = message[start:end]

    # Body, if the content header is present
    start = end + 2
    end = message.find(b'\r\n', start)
    if b'Content-Length' in headers and end != -1:
        body = bytes(message[start:int(headers[b'Content-Length'])])
    else:
        body = b''

    req = HTTPrequest(method, target, version, headers, body)

    return 200, req
