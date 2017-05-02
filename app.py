'''
Script for flask run
'''

import os
from pathlib import Path

from firewatch_hub import get_app

default_conf_path = 'firewatch-hub.yaml'

conf_file_path = os.environ.get('FIREWATCH_HUB_CONF')

if not conf_file_path:
    for p in 'firewatch-hub.yaml firewatch-hub.sample.yaml'.split():
        if Path(p).is_file():
            conf_file_path = p
            break

app = get_app(conf_file_path)
