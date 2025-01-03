import sys
import json
from MongoConnection import *
from DK_connection import make_get_request3
import datetime
import pytz

env = sys.argv[1] if 1 < len(sys.argv) else 'deployment'
db = getDb(env)
tz = pytz.timezone('Asia/Tehran')


class DataImporter():
    def __init__(self, dk_data, channel_id) -> None:
        self.dk_data = dk_data
        self.channel_id = channel_id
        self.old_product = db.products.find_one(
            {'DKPC': str(dk_data['product_variant_id'])})
        self.data_for_db = None

    def product_data_maker(self):
        if self.data_for_db:
            return self.data_for_db
        self.data_for_db = {
            'imageSrc': self.dk_data['image_src'],
            'name': self.dk_data['title'],
            'DKP': str(self.dk_data['product_id']),
            'DKPC': str(self.dk_data['product_variant_id']),
            'productGroup': self.dk_data['main_category_title'],
            'salesStatus': self.dk_data['active'],
            'channel': self.channel_id,
            'salesPrice': self.dk_data['price_sale'],
            'resourcePrice': self.dk_data['price_list'],
            'sellerStock': self.dk_data['marketplace_seller_stock'],
            'maximumPerOrder': self.dk_data['maximum_per_order'],
            'digikalaStock': self.dk_data['warehouse_stock'],
            'reservedStock': self.dk_data['reservation'],
            'supplierCode': self.dk_data['supplier_code'],
            'splitName': self.get_split_name(),
            'shippingOptions': self.get_shipping_options(),
            'otherSellerCount': self.otherSellerCount(),
            'active': True,
            'isUpdate': True,
            'nextChangePrice': datetime.datetime.now(tz),
            'lastGetToChangePrice': datetime.datetime.now(tz),
        }
        return self.data_for_db

    def get_old_product(self):
        return self.old_product

    def save_old_product(self):
        old_product = self.get_old_product()
        product = self.product_data_maker()
        if old_product['brand'] == "error":
            product['brand'] = "در حال دریافت"
        db.products.find_one_and_update(
            {'_id': old_product['_id']}, {'$set': product})
        product['brand'] = old_product['brand']
        db.productsBrandUpdate.insert_one(product)

    def save_new_product(self):
        product = self.product_data_maker()
        product['newName'] = product['name']
        product['robot'] = None
        same_product = db.products.find_one(
            {'DKP': str(product['DKP']), 'brand': {'$ne': 'در حال دریافت'}})
        if same_product:
            product['brand'] = same_product['brand']
        else:
            product['brand'] = "در حال دریافت"
        print('brand:', product['brand'])
        db.productsBrandUpdate.insert_one(product)
        db.products.insert_one(product)

    def save_to_db(self):
        old_product = self.get_old_product()
        if old_product:
            print('old_product')
            self.save_old_product()
            return
        print('new_product')
        self.save_new_product()

    def get_split_name(self):
        parts = self.dk_data['title'].split(' | ')
        if len(parts) >= 1:
            return parts[1].strip()
        return

    def get_shipping_options(self):
        if self.dk_data["shipping_options"]["is_fbd_active"] and self.dk_data["shipping_options"]["is_fbs_active"]:
            return "both"
        elif self.dk_data["shipping_options"]["is_fbd_active"]:
            return "digikala"
        return "seller"

    def otherSellerCount(self):
        if not self.dk_data['active']:
            return 0
        status, response = make_get_request3(
            url=f'https://api.digikala.com/v2/product/{self.dk_data["product_id"]}/', cookies={})
        if not status:
            print('digikala connection error')
            return 0
        res = json.loads(response.text)
        if not res:
            return 0
        variants = res.get('data', {}).get('product', {}).get('variants', [])
        if len(variants) == 0:
            return 0
        my_variant = [x for x in variants if str(
            x['id']) == str(self.dk_data['product_variant_id'])]
        if len(my_variant) == 0:
            my_competitors_without_vType = [
                i for i in variants[0] if 'color' in i or 'size' in i]
            if len(my_competitors_without_vType) == 0:
                otherSellerCount = len(variants)
                return otherSellerCount
            split_name = self.get_split_name()
            my_competitors = [i for i in variants if split_name in i.get('color', {}).get(
                'title', '') or split_name in i.get('size', {}).get('title', '')]
            if len(my_competitors) == 0:
                otherSellerCount = 0
                return otherSellerCount
            otherSellerCount = len(my_competitors)
            return otherSellerCount
        my_variant = my_variant[0]
        variant_type = None
        if 'size' in my_variant:
            variant_type = 'size'
        if 'color' in my_variant:
            variant_type = 'color'
        if not variant_type:
            my_competitors = sorted(
                variants, key=lambda x: x['rank'], reverse=True)
            return len(my_competitors) - 1
        my_competitors = [x for x in variants if str(
            x.get(variant_type, '')) == str(my_variant.get(variant_type))]
        my_competitors = sorted(
            my_competitors, key=lambda x: x['rank'], reverse=True)
        return len(my_competitors) - 1
