from bson import ObjectId
from datetime import datetime
import logging

from ..util import parse_date
from ..util.mongodb import connect_to_mongodb_conf


logger = logging.getLogger(__name__)


def get_model_from_conf(conf):
    db = connect_to_mongodb_conf(conf.hub_mongodb)
    return Model(db)


class Model:

    def __init__(self, db):
        self.c_agents = db['agents']
        self.c_events = db['events']

    def create_indexes(self):
        pass

    def update_agent_last_seen(self, agent_id, last_seen_date):
        assert isinstance(agent_id, str)
        assert isinstance(last_seen_date, datetime)
        q = {'agent_id': agent_id}
        up = {'$set': {'last_seen_date': last_seen_date}}
        self.c_agents.update_one(q, up, upsert=True)

    def insert_events(self, agent_id, host, events):
        assert isinstance(agent_id, str)
        assert isinstance(host, str)
        docs = []
        for event in events:
            docs.append({
                'agent_id': agent_id,
                'host': host,
                'log_path': event['log_path'],
                'date': parse_date(event['date']),
                'chunk': event['chunk'],
            })
        if docs:
            self.c_events.insert_many(docs, ordered=False)
            logger.info('Inserted %s events', len(docs))
