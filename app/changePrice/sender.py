import sys
import pika
import pymongo
import json
import asyncio
from bson import ObjectId
from datetime import datetime, timedelta

sys.path.insert(1, '../../')
import rabbitmqConnector as rabbit
from config import *

db = pymongo.MongoClient(config['database-server']['local'])["dk-robot"]

# MongoDB setup
product_collection = db['products']
account_collection = db['accounts']
channel_collection = db['channels']

# RabbitMQ setup
QUEUE_NAME = "product_queue"
rabbit_ch, rabbit_connection = rabbit.connect()
rabbit_ch.queue_declare(queue=QUEUE_NAME, durable=True)

channelId = "66b4fd91144ec10618f5aa8e"

async def fetch_and_send_products():
    # Fetch products associated with these channels
    products = product_collection.find({
        "channel": ObjectId(channelId),
        "_id":ObjectId("6777c3c0b9ad342524d31517"),
        "active": True,
        "nextChangePrice": {"$lte": datetime.now()},
        "lastGetToChangePrice": {"$lte": datetime.now() - timedelta(seconds=10)}
    }).sort("nextChangePrice", -1)

    for product in products:
        # Prepare product data with necessary channel and account information
        product_data = {
            '_id': str(product['_id']),
            'DKPC': product['DKPC'],
            'salesPrice':product['salesPrice'],
            'channel_id': str(product['channel']),
        }
        print(product_data)
        # Send product data to RabbitMQ queue
        rabbit_ch.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(product_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )
        # Update product's lastGetToChangePrice
        product_collection.update_one(
            {'_id': product['_id']},
            {'$set': {'lastGetToChangePrice': datetime.now()}}
        )
        return {"status":True}

async def scheduler():
    while True:
        await fetch_and_send_products()
        await asyncio.sleep(300)  # Wait for 5 minutes
