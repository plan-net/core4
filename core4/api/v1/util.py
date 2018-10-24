import json

import bson.objectid
import datetime
import numpy as np
import pandas as pd


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.datetime64):
            # this is a hack around pandas bug, see
            # http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64/13753918
            # we only observe this conversion requirements for dataframes with one and only one datetime column
            obj = pd.to_datetime(str(obj)).replace(tzinfo=None)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, bson.objectid.ObjectId):
            return str(obj)
        # what follows is based on
        # http://stackoverflow.com/questions/27050108/convert-numpy-type-to-python
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def json_encode(value):
    """JSON-encodes the given Python object."""
    return json.dumps(value, cls=JsonEncoder, indent=2)

def json_decode(value):
    if value:
        return json.loads(value)
    return None