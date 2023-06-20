from io import BytesIO
from socket import error

from modules.error_handling import Disconnect, CommandError, Error


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
