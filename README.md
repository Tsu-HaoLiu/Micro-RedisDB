# Micro-RedisDB


Start the database by running `./start_server.sh`

To test the server, launch a new python terminal 

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
