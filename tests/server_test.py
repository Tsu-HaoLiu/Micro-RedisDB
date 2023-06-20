import unittest
from unittest.mock import MagicMock

from server import Server
from modules.error_handling import Disconnect, CommandError, Error


class TestServer(unittest.TestCase):
    def test_get(self):
        server = Server()
        server._kv = {'key': 'value'}

        result = server.get('key')
        self.assertEqual(result, 'value')

    def test_set(self):
        server = Server()
        server.set('key', 'value')

        self.assertEqual(server._kv['key'], 'value')

    def test_delete_existing_key(self):
        server = Server()
        server._kv = {'key': 'value'}

        result = server.delete('key')
        self.assertEqual(result, 1)
        self.assertNotIn('key', server._kv)

    def test_delete_non_existing_key(self):
        server = Server()
        server._kv = {'key': 'value'}

        result = server.delete('nonexistent')
        self.assertEqual(result, 0)
        self.assertIn('key', server._kv)

    def test_flush(self):
        server = Server()
        server._kv = {'key1': 'value1', 'key2': 'value2'}

        result = server.flush()
        self.assertEqual(result, 2)
        self.assertEqual(len(server._kv), 0)

    def test_mget(self):
        server = Server()
        server._kv = {'key1': 'value1', 'key2': 'value2'}

        result = server.mget('key1', 'key2', 'key3')
        self.assertEqual(result, ['value1', 'value2', None])

    def test_mset(self):
        server = Server()

        result = server.mset('key1', 'value1', 'key2', 'value2')
        self.assertEqual(result, 2)
        self.assertEqual(server._kv['key1'], 'value1')
        self.assertEqual(server._kv['key2'], 'value2')

    def test_get_response_valid_command(self):
        server = Server()
        server._kv = {'key': 'result'}
        server.get = MagicMock(return_value='result')

        result = server.get_response(['GET', 'key'])
        self.assertEqual(result, 'result')

    def test_get_response_invalid_command(self):
        server = Server()

        with self.assertRaises(CommandError):
            server.get_response(['INVALID'])

    def test_get_response_invalid_request(self):
        server = Server()

        with self.assertRaises(CommandError):
            server.get_response('invalid request')


if __name__ == '__main__':
    unittest.main()
