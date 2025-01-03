import pymongo
from config import *


def getDb(env):
    return pymongo.MongoClient(config['database-server']['local'])["dk-robot"]
