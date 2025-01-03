from MongoConnection import *
import sys
from bson import ObjectId

env = sys.argv[1] if 1 < len(sys.argv) else 'deployment'
SLEEP_FOR_TOKEN = [0.2, 0.5, 0.8, 1, 1.5]


class TokenManager():
    def __init__(self, channel_id) -> None:
        self.channel_id = str(channel_id)
        self.channel = None
        self._db = getDb(env)

    def get(self):
        if self.version() == 'v2':
            return self.get_v2_token()

    def get_channel_db(self):
        if self.channel:
            return self.channel
        self.channel = self._db.channels.find_one(
            {'_id': ObjectId(self.channel_id)})
        return self.channel

    def get_v2_token(self):
        return self.get_channel_db()['token']

    def version(self):
        if self.get_channel_db().get('access_token'):
            return 'v3'
        return 'v2'
