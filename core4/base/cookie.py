import core4.base.main


class Cookie(core4.base.main.CoreBase):
    section = "job"

    def __init__(self, name=None):
        super().__init__()
        self.cookie_collection = self.config.sys.cookie
        self.name = name

    def set(self, *args, **kwargs):
        """
         Sets the cookie option to the passed value.

         :param option: of the cookie
         :param value: value to set
         :param kwargs: dictionary of options
         :return:
         """
        if args:
            if len(kwargs) > 0:
                raise RuntimeError('you cannot combine *args with **kwargs')
            kwargs[args[0]] = args[1]
        result = self.cookie_collection.update_one(filter={'_id': self.name},
                                                   update={'$set': kwargs},
                                                   upsert=True)
        return result.raw_result['n'] > 0

    def inc(self, field, value=1):
        """
        Increment a value attribute in the cookie.

        :param field: field name
        :param value: increment value, defautls to 1
        :return: True in case of success, else False
        """
        result = self.cookie_collection.update_one(filter={'_id': self.name},
                                                   update={'$inc': {
                                                       field: value
                                                   }}, upsert=False)
        return result.raw_result['n'] > 0

    def dec(self, field, value=1):
        """
        Decrements a value attribute in the cookie.

        :param field: field name
        :param value: decrement value, defautls to 1
        :return: True in case of success, else False
        """
        return self.inc(field, -1 * value)

    def max(self, field, value, **kwargs):
        """
        Sets the cookie option to the maximum current value.
        Compares the current value to the given value and sets the greater.


        :param field: field name
        :param value: value to compare
        """
        result = self.cookie_collection.update_one(filter={'_id': self.name},
                                                   update={
                                                       '$max': {field: value}},
                                                   upsert=True)
        return result.raw_result['nModified'] > 0

    def min(self, field, value, **kwargs):
        """
        Sets the cookie option to the minimum current value.
        Compares the current value to the given value and sets the lower.

        :param field: field name
        :param value: value to compare
        """
        result = self.cookie_collection.update_one(filter={'_id': self.name},
                                                   update={
                                                       '$min': {field: value}},
                                                   upsert=True)
        return result.raw_result['n'] > 0

    def get(self, option):
        """
        Get the cookie option value.

        :param option: of the cookie
        :return: option value
        """
        value = self.cookie_collection.find_one({'_id': self.name},
                                                projection={option: 1,
                                                            '_id': 0})
        if value and option in value:
            return value[option]
        return None

    def delete(self, option):
        """
        Deletes the option of a cookie.

        :param option: of the cookie
        """
        doc = self.cookie_collection.find_one({'_id': self.name})
        del doc[option]
        self.cookie_collection.find_one_and_replace(filter={'_id': self.name},
                                                    replacement=doc)

    def has_option(self, option):
        """
        Returns *True* if the cookie option exists.

        :param option:
        :return: True if the option exists, else False
        """
        doc = self.cookie_collection.find_one({'_id': self.name})
        return option in doc
