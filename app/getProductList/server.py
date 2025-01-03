from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException, Form
from datetime import datetime
import pytz
from bson import ObjectId
import traceback
import json
import sys
from TokenManager import TokenManager
from DK_connection import make_get_request3
from getProductList.sender import send_to_queue
sys.path.insert(1, '../../')
from MongoConnection import getDb
from config import *

env = sys.argv[1] if len(sys.argv) > 1 else 'deployment'
db = getDb(env)
tz = pytz.timezone('Asia/Tehran')

app = FastAPI()


channelId = "66b4fd91144ec10618f5aa8e"


def make_error(status_code, message):
    raise HTTPException(status_code=status_code, detail=message)


async def get_product_list(channelId: str = Form(...)):
    if not channelId:
        print(400, 'bad request')
        make_error(400, 'bad request')

    try:
        channelId = "66b4fd91144ec10618f5aa8e"
        tm = TokenManager(channelId)
        data = await get_data_from_dk(tm,channelId)
        if not data:
            make_error(500, 'something went wrong')
        await update_channel_and_products(data)
        data_for_queue = make_data(data)
        send_to_queue(data_for_queue)
        return {"success": True}
    except Exception as e:
        traceback.print_exc()
        make_error(500, 'something went wrong')


async def get_data_from_dk(token_manager,channelId):
    token = token_manager.get()
    version = token_manager.version()
    cookie = {
        'seller_api_access_token': token}
    url = 'https://seller.digikala.com/api/v2/variants?page=1&size=50'
    session, response = make_get_request3(url=url, cookies=cookie)

    print('Session', session)
    print('Response', response)
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
            "lastUpdate": datetime.now(tz),
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
