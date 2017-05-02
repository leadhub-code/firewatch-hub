from pathlib import Path
import yaml


class Configuration:

    def __init__(self, cfg_path):
        assert isinstance(cfg_path, Path)
        with cfg_path.open() as f:
            data = yaml.safe_load(f)
        cfg = data['firewatch_hub']
        cfg_dir = cfg_path.parent.resolve()
        self.secret_file = _SecretFile(cfg_dir / cfg['secret_file'])
        self.hub_mongodb = _MongoDB(cfg['hub_mongodb'], cfg_dir)
        self.login = _Login(cfg['login'], cfg_dir)


class _SecretFile:

    def __init__(self, path):
        self.path = path
        self.value = None

    def get_value(self):
        from uuid import uuid4
        if not self.value:
            try:
                with self.path.open() as f:
                    v = f.read().strip()
            except FileNotFoundError as e:
                v = None
            if not v:
                v = uuid4().hex
                with self.path.open('w') as f:
                    f.write(v + '\n')
            self.value = v
        assert self.value
        return self.value


class _MongoDB:

    def __init__(self, cfg, cfg_dir):
        self.uri = cfg['uri']
        self.db_name = cfg['db_name']
        self.ca_cert_file_path = None
        if cfg.get('ssl'):
            if cfg['ssl'].get('ca_cert_file'):
                self.ca_cert_file_path = cfg_dir / cfg['ssl']['ca_cert_file']


class _Login:

    def __init__(self, cfg, cfg_dir):
        self.allowed_emails = cfg['allowed_emails']
        assert isinstance(self.allowed_emails, list)
        self.oauth2_google = None
        if cfg.get('oauth2_google') and cfg['oauth2_google'].get('client_id'):
            self.oauth2_google = _OAuth2(cfg['oauth2_google'], cfg_dir)


class _OAuth2:

    def __init__(self, cfg, cfg_dir):
        self.client_id = cfg['client_id']
        self.client_secret = cfg['client_secret']
        self.redirect_uri = cfg['redirect_uri']
