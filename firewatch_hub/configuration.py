from pathlib import Path
import yaml


class Configuration:

    def __init__(self, cfg_path):
        assert isinstance(cfg_path, Path)
        with cfg_path.open() as f:
            data = yaml.safe_load(f)
        cfg = data['firewatch_hub']
        cfg_dir = cfg_path.parent.resolve()
        self.hub_mongodb = MongoDB(cfg['hub_mongodb'], cfg_dir)


class MongoDB:

    def __init__(self, cfg, cfg_dir):
        self.uri = cfg['uri']
        self.db_name = cfg['db_name']
        self.ca_cert_file_path = None
        if cfg.get('ssl'):
            if cfg['ssl'].get('ca_cert_file'):
                self.ca_cert_file_path = cfg_dir / cfg['ssl']['ca_cert_file']
