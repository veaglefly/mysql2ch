import datetime
import json
import logging
import sys
from decimal import Decimal

import dateutil.parser

logger = logging.getLogger("mysql2ch.common")

CONVERTERS = {
    "date": dateutil.parser.parse,
    "datetime": dateutil.parser.parse,
    "decimal": Decimal,
}


def init_logging(debug):
    """
    init logging config
    :param debug:
    :return:
    """
    base_logger = logging.getLogger("mysql2ch")
    if debug:
        base_logger.setLevel(logging.DEBUG)
    else:
        base_logger.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    base_logger.addHandler(sh)


def complex_decode(xs):
    if isinstance(xs, dict):
        ret = {}
        for k in xs:
            ret[k.decode()] = complex_decode(xs[k])
        return ret
    elif isinstance(xs, list):
        ret = []
        for x in xs:
            ret.append(complex_decode(x))
        return ret
    elif isinstance(xs, bytes):
        return xs.decode()
    else:
        return xs


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return {"val": obj.strftime("%Y-%m-%d %H:%M:%S"), "_spec_type": "datetime"}
        elif isinstance(obj, datetime.date):
            return {"val": obj.strftime("%Y-%m-%d"), "_spec_type": "date"}
        elif isinstance(obj, Decimal):
            return {"val": str(obj), "_spec_type": "decimal"}
        else:
            return super().default(obj)


def object_hook(obj):
    _spec_type = obj.get("_spec_type")
    if not _spec_type:
        return obj

    if _spec_type in CONVERTERS:
        return CONVERTERS[_spec_type](obj["val"])
    else:
        raise TypeError("Unknown {}".format(_spec_type))
