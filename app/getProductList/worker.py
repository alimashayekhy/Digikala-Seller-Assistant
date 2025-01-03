from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import pika
import json
import pytz
from datetime import datetime
from bson import ObjectId
import traceback
import sys

# Import your custom modules
sys.path.insert(1,'../../')
from TokenManager import TokenManager
from DK_connection import make_get_request3
import rabbitmqConnector as rabbit
from config import config
from MongoConnection import getDb
from getProductList.DataImporter import DataImporter

# Initialize FastAPI app
app = FastAPI()

# MongoDB setup
env = sys.argv[1] if 1 < len(sys.argv) else 'deployment'
db = getDb(env)
tz = pytz.timezone('Asia/Tehran')
QUEUE_NAME = config['getProductList']['queue_name']

# RabbitMQ connection
rabbit_ch, rabbit_connection = rabbit.connect()
rabbit_ch.queue_declare(queue=QUEUE_NAME, durable=True)

def serialize_defaults(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError("Type not serializable")


def make_error(ch, method, data):
    data['retry'] += 1
    ch.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=json.dumps(data, default=serialize_defaults),
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
    )


def callback(ch, method, properties, data):
    try:
        data = json.loads(data)
        if data['retry'] > 2:
            db.dataImporterLogs.insert_one({
                'channel': ObjectId(data['channel_id']),
                'page_number': data['page_number'],
                'date': datetime.now(tz)
            })
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        tm = TokenManager(data['channel_id'])
        token = tm.get()
        page_number = data["page_number"]
        print(page_number)
        channel_id = ObjectId(data['channel_id'])
        channel = db.channels.find_one({"_id": channel_id})
        total_product_counts = channel.get("totalProductCount")
        print('total_product_counts', total_product_counts)

        cookie = {'seller_api_access_token': token}
        url = f'https://seller.digikala.com/api/v2/variants?page={page_number}&size=50'
        status, response = make_get_request3(url=url, cookies=cookie)
        print('Status', status)

        if not status:
            make_error(ch, method, data)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        resp = json.loads(response.text)
        for index, item in enumerate(resp['data']['items']):
            di = DataImporter(item, channel_id)
            di.save_to_db()
            if index + 1 == len(resp['data']['items']):
                received_products_count = db.products.count_documents({
                    "channel": channel_id,
                    "isUpdate": True,
                    "active": True
                })
                print('received_products_count', received_products_count)
                if (total_product_counts == received_products_count):
                    db.channels.find_one_and_update(
                        {'_id': channel_id},
                        {'$set': {"isInUpdateProcess": False}}
                    )
                    db.products.update_many(
                        {"channel": channel_id, "isUpdate": False},
                        {'$set': {'active': False}}
                    )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return {"status":True}

    except Exception as e:
        traceback.print_exc()
        make_error(ch, method, data)
        ch.basic_ack(delivery_tag=method.delivery_tag)

def process_message(message):
    """
    Process the received message and push it to the RabbitMQ queue
    """

    # Start consuming messages asynchronously
    rabbit_ch.basic_qos(prefetch_count=1)
    rabbit_ch.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    rabbit_ch.start_consuming()

    return {'message':message.dict()}
