import sys
import pika
import json
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
from datetime import datetime
sys.path.insert(1,'../../')
from TokenManager import TokenManager
import rabbitmqConnector as rabbit
from MongoConnection import getDb
from config import *
from DK_connection import make_get_request3

env = sys.argv[1] if len(sys.argv) > 1 else 'deployment'
db = getDb(env)

QUEUE_NAME = config['getProductList']['queue_name']

app = FastAPI()


def serialize_defaults(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError("Type not serializable")


def send_to_queue(result):
    try:
        rabbit_ch, rabbit_connection = rabbit.connect()
        rabbit_ch.queue_declare(queue=QUEUE_NAME, durable=True)
        for data in result:
            dataToSend = {
                "channel_id": data['channel'],
                "page_number": data['page'],
                'retry': 0
            }
            print('send to queue: ', dataToSend)
            rabbit_ch.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=json.dumps(dataToSend, default=serialize_defaults),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
            )
        print('finished')
    except Exception as e:
        raise e
    except KeyboardInterrupt:
        rabbit_ch.close()
        print('interrupted!')


async def get_product_list(channelId: str = Form(...)):
    if not channelId:
        raise HTTPException(status_code=400, detail="Bad request")

    try:
        tm = TokenManager(channelId)
        data = await get_data_from_dk(tm, channelId)
        if not data:
            raise HTTPException(status_code=500, detail="Something went wrong")
        await update_channel_and_products(data)
        data_for_queue = make_data(data)
        send_to_queue(data_for_queue)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong")


async def get_data_from_dk(token_manager, channelId):
    token = token_manager.get()
    version = token_manager.version()
    if version == 'v2':
        cookie = {'seller_api_access_token': token}
        url = 'https://seller.digikala.com/api/v2/variants?page=1&size=50'
        session, response = make_get_request3(url=url, cookies=cookie)
    print('Session', session)
    if session:
        resp = json.loads(response.text)
        page_count = resp['data']['pager']["total_pages"]
        total_product_count = resp['data']['pager']["total_rows"]
        data = {
            "success": True,
            "channelId": channelId,
            "page_count": page_count,
            "total_product_count": total_product_count
        }

        return data


async def update_channel_and_products(data):
    db.channels.find_one_and_update({"_id": ObjectId(data["channelId"])}, {
        "$set": {
            "totalProductCount": data["total_product_count"],
            "lastUpdate": datetime.now(),
            "isInUpdateProcess": True
        }
    })
    db.products.update_many(
        {"channel": ObjectId(data["channelId"])},
        {"$set": {"isUpdate": False}}
    )


def make_data(data):
    result = []
    for i in range(1, data['page_count'] + 1):
        new_data = {
            "channel": data['channelId'],
            "page": i,
        }
        result.append(new_data)
    return result
