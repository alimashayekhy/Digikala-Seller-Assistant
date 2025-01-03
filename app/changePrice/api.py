import sys
sys.path.insert(1, '../../')
from DK_connection import make_put_request
import json
import traceback


def change_price(dkpc, price, token_manager):
    token = token_manager.get()
    version = token_manager.version()
    if version == 'v2':
        url = "https://seller.digikala.com/api/v2/variants/" + str(dkpc)

        payload = {
            "id": dkpc,
            "shipping_type": "digikala",
            "lead_time": 2,
            'seller_lead_time': 0,
            "selling_price": price
        }

        status, response = make_put_request(url, data=json.dumps(payload), MSL=str(token))

        status = True

    try:
        if version == 'v2':
            if response == 'DK_Error':
                return False, 'DK_Error'
            res_data = json.loads(response["text"])

        if status:
            if res_data["status"] == "ok":
                if res_data['data']["marketplace_seller_stock"] == 0 and res_data['data']["left_consumer"] == 0:
                    return False, "DK_Error: " + "موجودی این تنوع به پایان رسیده است"
                return True, True

            if type(res_data['errors']) is dict:  # if problem occurred in price, response doesn`t have any key!
                print("DK_Error: " + list(res_data["errors"].items())[0][1][0])
                return False, "DK_Error: " + list(res_data["errors"].items())[0][1][0]
            elif type(res_data['errors']) is list:
                return False, "DK_Error: " + res_data["errors"][0]

        else:
            print("digikala error")
            return False, "DK_Error"
    except:
        print("change price error")
        traceback.print_exc()
        return False, "DK_Error"
    return False, "DK_Error"


def reactive_product(dkpc, token_manager, product_info):
    version = token_manager.version()
    token = token_manager.get()
    if product_info["resourcePrice"] > 0:
        if product_info["maxPrice"] >= product_info['resourcePrice'] >= product_info["minPrice"]:
            round_price = int(str(product_info['resourcePrice'])[:-2] + '00')
            status, response = change_price(dkpc, round_price, token_manager, product_info)
            if status:
                if version == 'v2':
                    url = "https://seller.digikala.com/api/v2/variants/" + \
                    str(dkpc) + "/activation"
                    payload = json.dumps({
                        "activation": True
                    })
                    status, response = make_put_request(url, data=payload, MSL=str(token))

                    res_data = json.loads(response["text"])

                if res_data["status"] == "ok":
                    return True, ""
                else:
                    if "errors" in res_data:
                        if type(res_data['errors']) is dict:  # if problem occurred in price, response doesn`t have any key!
                            print("DK_Error: " + list(res_data["errors"].items())[0][1][0])
                            return False, "DK_Error: " + list(res_data["errors"].items())[0][1][0]
                        elif type(res_data['errors']) is list:
                            return False, "DK_Error: " + res_data["errors"][0]

                    return False, "reactivation_error"
            else:
                return False, response
        else:
            if product_info['resourcePrice'] > product_info['maxPrice']:
                if product_info['maxPrice'] > product_info['resourcePrice'] * 0.75:
                    round_price = int(str(product_info['maxPrice'])[:-2] + '00')
                    status, response = change_price(dkpc, round_price, token_manager, product_info)
                    if status:
                        if version == 'v2':
                            url = "https://seller.digikala.com/api/v2/variants/" + \
                            str(dkpc) + "/activation"
                            payload = json.dumps({
                                "activation": True
                            })
                            status, response = make_put_request(url, data=payload, MSL=str(token))

                            res_data = json.loads(response["text"])

                        if res_data["status"] == "ok":
                            return True, ""
                        else:
                            if "errors" in res_data:
                                if type(res_data['errors']) is dict:  # if problem occurred in price, response doesn`t have any key!
                                    print("DK_Error: " + list(res_data["errors"].items())[0][1][0])
                                    return False, "DK_Error: " + list(res_data["errors"].items())[0][1][0]
                                elif type(res_data['errors']) is list:
                                    return False, "DK_Error: " + res_data["errors"][0]

                            return False, "reactivation_error"
                    else:
                        return False, response
                else:
                    return False, "reactivation_error: " + "قیمت فعالسازی مجدد خارج از بازه حداقل و حداکثر قیمت مشخص شده است"
            elif product_info['resourcePrice'] < product_info['minPrice']:
                round_price = int(str(product_info['minPrice'])[:-2] + '00') + 100 # + 100 becouse it goes in range 
                status, response = change_price(dkpc, round_price, token_manager, product_info)
                if status:
                    if version == 'v2':
                        url = "https://seller.digikala.com/api/v2/variants/" + \
                        str(dkpc) + "/activation"
                        payload = json.dumps({
                            "activation": True
                        })
                        status, response = make_put_request(url, data=payload, MSL=str(token))

                        res_data = json.loads(response["text"])

                    if res_data["status"] == "ok":
                        return True, ""
                    else:
                        if "errors" in res_data:
                            if type(res_data['errors']) is dict:  # if problem occurred in price, response doesn`t have any key!
                                print("DK_Error: " + list(res_data["errors"].items())[0][1][0])
                                return False, "DK_Error: " + list(res_data["errors"].items())[0][1][0]
                            elif type(res_data['errors']) is list:
                                return False, "DK_Error: " + res_data["errors"][0]


                        return False, "reactivation_error"
                else:
                    return False, response
    #active product with min Price if there is no resourcePrice
    else:
        round_price = int(str(product_info['minPrice'])[:-2] + '00') + 100 # + 100 becouse it goes in range 
        status, response = change_price(dkpc, round_price, token_manager, product_info)
        if status:
            if version == 'v2':
                url = "https://seller.digikala.com/api/v2/variants/" + \
                str(dkpc) + "/activation"
                payload = json.dumps({
                    "activation": True
                })
                status, response = make_put_request(url, data=payload, MSL=str(token))

                res_data = json.loads(response["text"])

            if res_data["status"] == "ok":
                return True, ""
            else:
                if "errors" in res_data:
                    if type(res_data['errors']) is dict:  # if problem occurred in price, response doesn`t have any key!
                        print("DK_Error: " + list(res_data["errors"].items())[0][1][0])
                        return False, "DK_Error: " + list(res_data["errors"].items())[0][1][0]
                    elif type(res_data['errors']) is list:
                        return False, "DK_Error: " + res_data["errors"][0]


                return False, "reactivation_error"
        else:
            return False, response