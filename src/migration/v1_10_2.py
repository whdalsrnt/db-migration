import logging
from conf import DEFAULT_LOGGER
from pymongo import UpdateOne
from lib import MongoCustomClient
from lib.util import query

_LOGGER = logging.getLogger(DEFAULT_LOGGER)


@query
def inventory_cloud_service_tags_refactoring(mongo_client: MongoCustomClient):
    items = mongo_client.find('INVENTORY', 'cloud_service', {}, {'provider': 1, 'tags': 1})
    operations = []
    for item in items:
        provider = item.get('provider', '')
        if isinstance(item['tags'], list):
            operations.append(
                UpdateOne({'_id': item['_id']},
                          {"$set": {"tags": _change_tags_to_list_of_dict(_change_tags(item['tags']), provider)}})
            )
        elif isinstance(item['tags'], dict):
            operations.append(
                UpdateOne({'_id': item['_id']},
                          {"$set": {"tags": _change_tags_to_list_of_dict(item['tags'], provider)}})
            )

    mongo_client.bulk_write('INVENTORY', 'cloud_service', operations)


def _change_tags(data):
    """ convert tags type ( list of dict -> dict )
    [AS-IS]
            1) general type >>> {"tags": [{key: 'type', value: 'test'}, {key: 'user', value: 'developer'}]}
            2) empty list   >>> {"tags": []}
            3) dict type    >>> {"tags":{"type":"test"}}
    [TO-BE]
            1) general type >>>  {"tags": {'type':'test', 'user':'developer'}}
            2) empty list   >>>  {"tags":{}}
            3) dict type    >>> {"tags":{"type":"test"}}
    """
    new_dict = {}
    if not len(data):
        return new_dict
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        for index in range(len(data)):
            new_dict[data[index]["key"]] = data[index].get("value", "")
    return new_dict


def _change_tags_to_list_of_dict(dict_values: dict, provider: str) -> list:
    tags = []
    for key, value in dict_values.items():
        new_tag = {
            'key': key,
            'value': value,
            'type': 'MANAGED',
            'provider': provider
        }
        tags.append(new_tag)
    return tags


def main(file_path, debug):
    mongo_client: MongoCustomClient = MongoCustomClient(file_path, debug)
    inventory_cloud_service_tags_refactoring(mongo_client)
