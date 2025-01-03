import configparser
from fastapi import FastAPI, Request
from pydantic import BaseModel
import sys
sys.path.insert(1,'../')
from app.getProductList import server
from app.getProductList import worker
from app.changePrice import sender
from app.changePrice import changeWorker

config = configparser.ConfigParser()
config.read('../config.cfg')

app = FastAPI()

class MessageData(BaseModel):
    channel_id: str
    page_number: int
    retry: int = 0

@app.post("/getProductList")
async def get_product_list(request: Request):
    return await server.get_product_list(request)

@app.post("/prepareProductList/")
async def process_message(message: MessageData):
    return await worker.process_message(message)

@app.post("/getPrice/")
async def scheduler():
    return await sender.scheduler()

@app.post("/changePrice/")
async def process_message():
    return await changeWorker.consume_products()



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0" ,port=int(
        config['getProductList-server']['port']))
