# Miniature RedisDB

This is a miniature Redis-like in-memory key-value store implemented in Python.

## Features

- Key-value storage in memory
- Support for basic Redis commands: SET, GET, DELETE, FLUSH, MGET, MSET 
- Multi-threaded handling of requests using gevent

## Usage

Start the database by running `./start_server.sh`

RedisDB server will start on 127.0.0.1 port 31337. You can then connect to it with sockets or using the client module included in repo:

```
>>> from modules.client import Client
>>> client = Client()
>>> client.mset('key1', 'value1', 'key2', 'value2', 'key3', ['value_list1', 'value_list2', 5], 'key4', 4)
4
>>> client.set('key_dict', {'value_dict': {'inner_value': 0, 'inner_value2': ['list1', 2, 3]}})
1
>>> client.get('key_dict')
{'value_dict': {'inner_value': 0, 'inner_value2': ['list1', 2, 3]}}
>>> client.mget('key2', 'key4', 'key_dict')
['value2', 4, {'value_dict': {'inner_value': 0, 'inner_value2': ['list1', 2, 3]}}]
>>> client.delete('key2')
1
>>> client.mget('key2', 'key4', 'key_dict')
[None, 4, {'value_dict': {'inner_value': 0, 'inner_value2': ['list1', 2, 3]}}]

```

## Commands 

- SET - Set the value for a key
- GET - Get the value for a key
- DELETE - Delete a key
- FLUSH - Delete all keys
- MGET - Get multple values at once
- MSET - Set multple values at once

---
## TODO

This is a minimal implementation to demonstrate a simple Redis-like server in Python. 
Further improvements could include:

- Support for more Redis commands
- More robust error handling and logging
- Support client disconnects and subsequent reconnections
