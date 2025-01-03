Messages = {
        'DKPC': product_data['DKPC'],
        'productId': str(product_data['_id']),
        'previousPrice': product_data['salesPrice'],
        'newPrice': new_price if api_response else "Price didn't update",
        'when': datetime.now(),
        'status': 'SUCCESSFULLY' if api_response else 'ERROR',
        'APIResponse': api_response if isinstance(api_response, str) else json.dumps(api_response)
    }