from DK_connection import make_get_request3
from api import reactive_product
import json


def product_detail(dkpc, token_manager, reactivation, robot_details, is_variant=True, can_reactive=True):
    """
    Returned data structure:
    
    - status: False on failure, True on success
    - response: Self side generated response code
    - product_info: New structure product info
    - variants: Returned variants from digikala response
    """
    version = token_manager.version()
    token = token_manager.get()
    if version == 'v2':
        url = 'https://seller.digikala.com/api/v2/variants?page=1&size=1&search[search_term]='+dkpc+'&sort=product_variant_id&order=desc'
        cookie = {'seller_api_access_token': token}

        status, response = make_get_request3(url, cookies=cookie)

    product_info = {'dkpc': dkpc}
    if status:
        try:
            if version == 'v2':
                json_res = json.loads(response.text)
            if len(json_res) != 0:
                response = json_res['data']['items'][0]
                dkp = response['product_id']
                product_info['dkpc'] = dkpc
                product_info['dkp'] = dkp
                product_info['lead_time'] = response['lead_time']
                product_info['marketplace_seller_stock'] = response['marketplace_seller_stock']
                product_info['maximum_per_order'] = response['maximum_per_order']
                product_info['salesStatus'] = response['active']
                product_info['salesPrice'] = int(response['price_sale'])
                product_info['resourcePrice'] = response['price_list']
                product_info['sellerStock'] = response['marketplace_seller_stock']
                product_info['digikalaStock'] = response['warehouse_stock']
                product_info['digikalaReservation'] = response['digikala_reservation']
                product_info['reservedStock'] = response['reservation']
                product_info['resourcePrice'] = response['price_list']
                product_info['buy_box_price'] = response['buy_box_price']
                product_info['promo_price'] = response["promotion_price"]
                product_info['is_in_promotion'] = False
                product_info['seller_shipping_lead_time'] = response["seller_shipping_lead_time"]
                product_info['errorText'] = ""

                product_info['brand'] = "در حال دریافت"

                if product_info['promo_price']:
                    product_info['is_in_promotion'] = True

                # check shipping by:
                if response["shipping_options"]["is_fbd_active"] and response["shipping_options"]["is_fbs_active"]:
                    product_info["shippingOptions"] = "both"
                elif response["shipping_options"]["is_fbd_active"]:
                    product_info["shippingOptions"] = "digikala"
                else:
                    product_info["shippingOptions"] = "seller"
                    # product_info['lead_time'] = floor(response["seller_shipping_lead_time"]/24)

                reactivation_error = ""
                product_info['isActive'] = response["active"]
                # print('can_reactive', can_reactive)
                if not product_info['isActive'] and reactivation == "enable" and can_reactive:
                    product_info["maxPrice"] = robot_details["maxPrice"]
                    product_info["minPrice"] = robot_details["minPrice"]
                    product_info['isActive'], reactivation_error = reactive_product(dkpc, token_manager, product_info)

                if product_info['isActive']:
                    status, response = make_get_request3(url='https://api.digikala.com/v2/product/' + str(dkp) + '/', #changed!!!
                                                         cookies={})
                    if status:
                        variants = json.loads(response.text)['data']['product']['variants']
                        if len(variants) > 0:
                            my_variant = [x for x in variants if str(x['id']) == str(dkpc)]
                            if len(my_variant) > 0:
                                if not is_variant:
                                    my_competitors = [x for x in variants if
                                                      str(x["seller"]["id"]) != str(my_variant[0]["seller"]["id"])]

                                    sorted_variants = sorted(variants, key=lambda x: x['rank'], reverse=True)
                                    product_info['inByBox'] = sorted_variants[0]['id'] == my_variant[0]['id']
                                    product_info['otherSellerCount'] = len(my_competitors)
                                    product_info['name'] = sorted_variants[0]['seller']['title']
                                    product_info['inBox_price'] = sorted_variants[0]['price']['selling_price']
                                    return True, "", product_info, variants
                                else:
                                    my_variant = my_variant[0]
                                    variant_type = None
                                    if 'size' in my_variant:
                                        variant_type = 'size'
                                    if 'color' in my_variant:
                                        variant_type = 'color'
                                    if variant_type:
                                        my_competitors = [x for x in variants if
                                                          str(x[variant_type]) == str(my_variant[variant_type])]
                                        my_competitors = sorted(my_competitors, key=lambda x: x['rank'], reverse=True)
                                    else:
                                        my_competitors = sorted(variants, key=lambda x: x['rank'], reverse=True)
                                    product_info['inByBox'] = my_competitors[0]['id'] == my_variant['id']
                                    product_info['otherSellerCount'] = len(my_competitors) - 1
                                    product_info['name'] = my_competitors[0]['seller']['title']
                                    product_info['inBox_price'] = my_competitors[0]['price']['selling_price']
                                    return True, "", product_info, variants
                            else:
                                product_info['inByBox'] = False
                                product_info['otherSellerCount'] = None
                                product_info['name'] = "ناموجود"
                                product_info['inBox_price'] = 0
                                return False, "no_stock", product_info, None
                        else:
                            product_info['inByBox'] = False
                            product_info['otherSellerCount'] = 0
                            product_info['name'] = "ناموجود"
                            product_info['inBox_price'] = 0
                            return False, "no_stock", product_info, None
                    else:
                        # print('digikala connection error')
                        return False, "DK_Error", product_info, None
                else:
                    # print("DeActive")
                    product_info['name'] = ""
                    product_info['inBox_price'] = ""
                    product_info['inByBox'] = False
                    product_info['otherSellerCount'] = None
                    if reactivation_error:
                        return False, reactivation_error, product_info, None
                    return False, "DeActive", product_info, None
            else:
                # print("DeActive")
                product_info['name'] = ""
                product_info['inBox_price'] = ""
                product_info['inByBox'] = False
                product_info['otherSellerCount'] = None
                return False, "DeActive", product_info, None
        except Exception as e:
            print('DK_Error (line 233-getDetails):', e)
            return False, "DK_Error", product_info, None

    elif response == "loginFailed":
        print("loginFailed")
        return False, "loginFailed", product_info, None

    else:
        print('digikala connection error')
        return False, "DK_Error", product_info, None