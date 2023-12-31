import unittest
from unittest.mock import MagicMock

from modules.protocol import ProtocolHandler
from modules.error_handling import Disconnect, CommandError, Error


class TestProtocolHandler(unittest.TestCase):
    def test_handle_simple_string(self):
        protocol_handler = ProtocolHandler()
        socket_file = MagicMock()
        socket_file.readline.return_value = b'OK\r\n'

        result = protocol_handler.handle_simple_string(socket_file)
        self.assertEqual(result, 'OK')

    def test_handle_error(self):
        protocol_handler = ProtocolHandler()
        socket_file = MagicMock()
        socket_file.readline.return_value = b'Error message\r\n'

        result = protocol_handler.handle_error(socket_file)
        self.assertEqual(result, Error('Error message'))

    def test_handle_integer(self):
        protocol_handler = ProtocolHandler()
        socket_file = MagicMock()
        socket_file.readline.return_value = b'42\r\n'

        result = protocol_handler.handle_integer(socket_file)
        self.assertEqual(result, 42)

    def test_handle_string(self):
        socket_file = MagicMock()
        socket_file.readline.return_value = b"10\r\n"
        socket_file.read.return_value = b"Hello World\r\n"

        result = ProtocolHandler().handle_string(socket_file)

        socket_file.readline.assert_called_once()
        socket_file.read.assert_called_once_with(12)
        self.assertEqual(result, b"Hello World")

    def test_handle_string_null(self):
        protocol_handler = ProtocolHandler()
        socket_file = MagicMock()
        socket_file.readline.return_value = b'-1\r\n'

        result = protocol_handler.handle_string(socket_file)
        self.assertIsNone(result)

    def test_handle_array(self):
        socket_file = MagicMock()
        socket_file.readline.return_value = b"3\r\n"
        socket_file.read.return_value = b"A"

        protocol_handler = ProtocolHandler()
        protocol_handler.handle_request = MagicMock(side_effect=[1, 2, 3])

        result = protocol_handler.handle_array(socket_file)

        socket_file.readline.assert_called_once()
        self.assertEqual(result, [1, 2, 3])

    def test_write_response_invalid_type(self):
        protocol_handler = ProtocolHandler()
        buf = MagicMock()
        data = object()

        with self.assertRaises(CommandError):
            protocol_handler._write(buf, data)


if __name__ == '__main__':
    unittest.main()
