from datetime import datetime
import re
import reprlib


_repr_obj = reprlib.Repr()
smart_repr = _repr_obj.repr


def parse_date(s):
    try:
        assert isinstance(s, str)
        if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}$', s):
            return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
    except Exception as e:
        raise Exception('Failed to parse date {!r}: {!r}'.format(s, e)) from e
    raise Exception('Failed to parse date {!r}: unknown format'.format(s))


assert parse_date('2017-05-02T11:23:04.639799') == datetime(2017, 5, 2, 11, 23, 4, 639799)
