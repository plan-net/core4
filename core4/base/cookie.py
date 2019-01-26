"""
This module provides core4 :class:`.Cookie`. Cookies allow state transitions
of otherwise stateless entities, i.e. :class:`.CoreJob` and
:class:`.CoreRequestHandler`.
"""


class Cookie:
    """
    Jobs and API resources have read/write access to a cookie identified by a
    name (both, jobs and resources are supposed to specify its
    :meth:`.qual_name` as the cookie name). The cookie allows state transitions 
    of otherwise stateless entities. The cookie essentially is a key/value 
    store. 
    
    The mongo document structure is::

        {
            "_id" : "long.qual.name",
            "test_key_1" : 123,
            "test_key_2" : 456,
        }

    Get and set a cookie key with::

        Cookie('long.qual.name').get('test_key_1')
        Cookie('long.qual.name').set('test_key_2', 789)
    """

    def __init__(self, name, collection):
        super().__init__()
        self.cookie_collection = collection
        self.cookie_name = name

    def set(self, *args, **kwargs):
        """
         Sets the cookie key to the passed value. There are two syntax
         alternatives::

            cookie.set(a, 1)
            cookie.set(a=1)

         :param args: key and value to set
         :param kwargs: dictionary of key/values
         :return: ``True`` if the key has been updated, else ``False``
         """
        if args:
            if len(kwargs) > 0:
                raise RuntimeError('you cannot combine *args with **kwargs')
            kwargs[args[0]] = args[1]
        result = self.cookie_collection.update_one(
            filter={'_id': self.cookie_name},
            update={'$set': kwargs},
            upsert=True)
        return result.raw_result['n'] > 0

    def inc(self, key, value=1):
        """
        Increment a value attribute in the cookie.

        :param key: str
        :param value: increment value, defautls to 1
        :return: ``True`` in case of success, else ``False``
        """
        result = self.cookie_collection.update_one(
            filter={'_id': self.cookie_name},
            update={
                '$inc': {key: value}
            }, upsert=False)
        return result.raw_result['n'] > 0

    def dec(self, key, value=1):
        """
        Decrement a value attribute in the cookie.

        :param key: str
        :param value: decrement value, defautls to 1
        :return: ``True`` in case of success, else ``False``
        """
        return self.inc(key, -1 * value)

    def max(self, key, value):
        """
        Sets the cookie key to the maximum comparing the current value with
        the given value.

        :param key: str
        :param value: value to compare and set
        """
        result = self.cookie_collection.update_one(
            filter={'_id': self.cookie_name},
            update={
                '$max': {key: value}
            },
            upsert=True)
        return result.raw_result['nModified'] > 0

    def min(self, key, value):
        """
        Sets the cookie key to the minimum comparing the current value with the
        given value.

        :param key: str
        :param value: value to compare and set
        """
        result = self.cookie_collection.update_one(
            filter={'_id': self.cookie_name},
            update={
                '$min': {key: value}
            },
            upsert=True)
        return result.raw_result['n'] > 0

    def get(self, key):
        """
        Get the value of the cookie key.

        :param key: str
        :return: value or ``None`` if the key does not exist
        """
        value = self.cookie_collection.find_one(
            {'_id': self.cookie_name}, projection={key: 1, '_id': 0})
        if value and key in value:
            return value[key]
        return None

    def delete(self, key):
        """
        Deletes the cookie key.

        :param key: str
        :return: ``True`` if the key has been removed, else ``False``
        :return: option value or ``None`` if the key does not exist
        """
        result = self.cookie_collection.update_one(
            filter={'_id': self.cookie_name},
            update={'$unset': {key: 1}})
        return result.raw_result['n'] > 0

    def has_key(self, key):
        """
        :param key: str
        :return: ``True`` if the key exists, else ``False``
        """
        doc = self.cookie_collection.find_one({'_id': self.cookie_name})
        return key in doc
