import pymongo
import json
import sys
from bson import ObjectId
from datetime import datetime
from changePrice.api import change_price
from changePrice.tools import error_handler

sys.path.insert(1, '../../')
import rabbitmqConnector as rabbit
from MongoConnection import getDb
from config import *
from TokenManager import TokenManager

db = pymongo.MongoClient(config['database-server']['local'])["dk-robot"]

# MongoDB setup
product_collection = db['products']
account_collection = db['accounts']
channel_collection = db['channels']
changelog_collection = db['change_logs']

# RabbitMQ setup
QUEUE_NAME = "product_queue"
rabbit_ch, rabbit_connection = rabbit.connect()
rabbit_ch.queue_declare(queue=QUEUE_NAME, durable=True)

channelId = "66b4fd91144ec10618f5aa8e"


def update_product_price(product_data):
    # Increase price by 10%
    new_price = round(product_data['salesPrice'] * 1.10 / 100) * 100
    # Simulate API call to update price
    api_response = dkNormalChangePrice(product_data, new_price)
    messages = {
        'DKPC': product_data['DKPC'],
        'productId': str(product_data['_id']),
        'previousPrice': product_data['salesPrice'],
        'newPrice': new_price if api_response else "Price didn't update",
        'when': datetime.now(),
        'status': 'SUCCESSFULLY' if api_response else 'ERROR',
        'APIResponse': api_response if isinstance(api_response, str) else json.dumps(api_response)
    }
    if api_response:
        print("yesssssss")
        # Update product price in the database
        product_collection.update_one(
            {'_id': ObjectId(product_data['_id'])},
            {'$set': {'salesPrice': new_price}}
        )
        print(f"Updated product {product_data['_id']} to new price {new_price}")
    else:
        print(f"Failed to update product {product_data['_id']}")
    changelog_collection.insert_one(messages)
    print(f"Changelog saved for product {product_data['DKPC']}")
    return

def dkNormalChangePrice(product_data,new_price):           
    status, response = change_price(product_data['DKPC'], new_price,TokenManager(product_data['channel_id']))
    if not status:
        error_handler(response, product_data['channel_id'], dkpc=product_data['DKPC'])
        return False
    if status:
            print("Status:",status)
            print("Response from digikala:",response)
            product_data['salesPrice'] = new_price
            return {'success': True}
def consume_products():
    def callback(ch, method, properties, body):
        product_data = json.loads(body)
        update_product_price(product_data)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    rabbit_ch.basic_qos(prefetch_count=1)
    rabbit_ch.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    rabbit_ch.start_consuming()
    return {"status":True}