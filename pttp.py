'''
Implementations for HTTP parsing request and building responses
'''

METHODS = (b'GET', b'HEAD', b'POST', b'OPTIONS')
END = b'\r\n\r\n'

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
        self.target = target

    def __str__(self):
        return '%s %s %s' % (
            self.method.decode(), self.target.decode(), self.version.decode(),)


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
        # Body
        if request.target == b'/':
            target = b'src/html/index.html'
        else:
            target = request.target[1:]

        # Check for 404
        try:
            with open(file=target.decode(), mode='rb') as tfile:
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

    # Body, if any
    start = end + 2
    end = message.find(b'\r\n', start)
    if b'Content-Length' in headers and end != -1:
        # Content header indicates there is a request body
        body = bytes(message[start:int(headers[b'Content-Length'])])
    else:
        body = b''

    req = HTTPrequest(method, target, version, headers, body)

    return 200, req
