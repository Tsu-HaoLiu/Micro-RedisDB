from gevent import socket
from gevent.pool import Pool
from gevent.server import StreamServer

from collections import namedtuple
from io import BytesIO
from socket import error


# Exceptions to notify the connection-handling loop of problems.
class CommandError(Exception):
    pass

class Disconnect(Exception):
    pass


Error = namedtuple('Error', ('message',))

class ProtocolHandler(object):
    def __init__(self):
        self.handlers = {
            b'+': self.handle_simple_string,
            b'-': self.handle_error,
            b':': self.handle_integer,
            b'$': self.handle_string,
            b'*': self.handle_array,
            b'%': self.handle_dict
        }

    def handle_request(self, socket_file):
        first_byte = socket_file.read(1)

        if not first_byte:
            raise Disconnect()

        try:
            # Delegate to the appropriate handler based on the first byte.
            return self.handlers[first_byte](socket_file)
        except KeyError:
            raise CommandError('bad request')

    @staticmethod
    def handle_simple_string(socket_file):
        return socket_file.readline().decode('utf-8').rstrip('\r\n')

    @staticmethod
    def handle_error(socket_file):
        return Error(socket_file.readline().decode('utf-8').rstrip('\r\n'))

    @staticmethod
    def handle_integer(socket_file):
        return int(socket_file.readline().decode('utf-8').rstrip('\r\n'))

    @staticmethod
    def handle_string(socket_file):
        # First read the length ($<length>\r\n).
        length = int(socket_file.readline().decode('utf-8').rstrip('\r\n'))
        if length == -1:
            return None  # Special-case for NULLs.
        length += 2  # Include the trailing \r\n in count.
        return socket_file.read(length)[:-2]

    def handle_array(self, socket_file):
        num_elements = int(socket_file.readline().decode('utf-8').rstrip('\r\n'))
        return [self.handle_request(socket_file) for _ in range(num_elements)]

    def handle_dict(self, socket_file):
        num_items = int(socket_file.readline().decode('utf-8').rstrip('\r\n'))
        elements = [self.handle_request(socket_file)
                    for _ in range(num_items * 2)]
        return dict(zip(elements[::2], elements[1::2]))

    def write_response(self, socket_file, data):
        buf = BytesIO()
        self._write(buf, data)
        buf.seek(0)
        # print(f'Fixed values -> {buf.getvalue()}')
        socket_file.write(buf.getvalue())
        socket_file.flush()

    def _write(self, buf, data):
        if isinstance(data, bytes):
            buf.write(bytes(f'${str(len(data))}\r\n{data}\r\n', encoding='utf-8'))
        elif isinstance(data, str):
            buf.write(bytes(f'+{data}\r\n', encoding='utf-8'))
        elif isinstance(data, int):
            buf.write(bytes(f':{data}\r\n', encoding='utf-8'))
        elif isinstance(data, Error):
            buf.write(bytes(f'-{error.message}\r\n', encoding='utf-8'))
        elif isinstance(data, (list, tuple)):
            buf.write(bytes(f'*{str(len(data))}\r\n', encoding='utf-8'))
            for item in data:
                self._write(buf, item)
        elif isinstance(data, dict):
            buf.write(bytes(f'%{str(len(data))}\r\n', encoding='utf-8'))
            for key in data:
                self._write(buf, key)
                self._write(buf, data[key])
        elif data is None:
            buf.write(bytes('$-1\r\n', encoding='utf-8'))
        else:
            raise CommandError('unrecognized type: %s' % type(data))


class Server(object):
    def __init__(self, host='127.0.0.1', port=31337, max_clients=64):
        self._pool = Pool(max_clients)
        self._server = StreamServer(
            (host, port),
            self.connection_handler,
            spawn=self._pool,
        )

        self._protocol = ProtocolHandler()
        self._kv = {}

        self._commands = self.get_commands()

    def get_commands(self):
        return {
            'GET': self.get,
            'SET': self.set,
            'DELETE': self.delete,
            'FLUSH': self.flush,
            'MGET': self.mget,
            'MSET': self.mset,
        }

    def get(self, key):
        return self._kv.get(key)

    def set(self, key, value):
        self._kv[key] = value
        return 1

    def delete(self, key):
        if key in self._kv:
            del self._kv[key]
            return 1
        return 0

    def flush(self):
        kv_len = len(self._kv)
        self._kv.clear()
        return kv_len

    def mget(self, *keys):
        return [self._kv.get(key) for key in keys]

    def mset(self, *items):
        data = zip(items[::2], items[1::2])
        for key, value in data:
            self._kv[key] = value
        return len(list(data))

    def connection_handler(self, conn, address):
        print('Connection received: %s:%s' % address)
        # Convert "conn" (a socket object) into a file-like object.
        socket_file = conn.makefile('rwb')

        # Process client requests until client disconnects.
        while True:
            try:
                data = self._protocol.handle_request(socket_file)
            except Disconnect:
                print('Client went away: %s:%s' % address)
                break

            try:
                resp = self.get_response(data)
            except CommandError as exc:
                resp = Error(exc.args[0])

            self._protocol.write_response(socket_file, resp)

    def get_response(self, data):

        if not isinstance(data, list):
            try:
                data = data.split()
            except Exception as e:
                raise CommandError('Request must be list or simple string.', e)

        if not data:
            raise CommandError('Missing command')

        command = data[0].upper()
        if command not in self._commands:
            raise CommandError('Unrecognized command: %s' % command)

        print(f'Received {command} command')
        return self._commands[command](*data[1:])

    def run(self):
        self._server.serve_forever()


class Client(object):
    def __init__(self, host='127.0.0.1', port=31337):
        self._protocol = ProtocolHandler()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))
        self._fh = self._socket.makefile('rwb')

    def execute(self, *args):
        print(f'Heard response from client {args[0]}: {args}')

        self._protocol.write_response(self._fh, args)
        resp = self._protocol.handle_request(self._fh)
        if isinstance(resp, Error):
            raise CommandError(resp.message)
        return resp

    def get(self, key):
        return self.execute('GET', key)

    def set(self, key, value):
        return self.execute('SET', key, value)

    def delete(self, key):
        return self.execute('DELETE', key)

    def flush(self):
        return self.execute('FLUSH')

    def mget(self, *keys):
        return self.execute('MGET', *keys)

    def mset(self, *items):
        return self.execute('MSET', *items)


if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()
    Server().run()
