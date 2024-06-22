import requests
import json
import time
import hmac
import base64
import hashlib
import os
import signal
from datetime import datetime, timezone

# API Keys and Secrets
OKX_API_KEY = ''
OKX_API_SECRET = ''
OKX_API_PASS = ''

BITGET_API_KEY = ''
BITGET_API_SECRET = ''
BITGET_API_PASS = ''

# API URLs
OKX_BASE_URL = 'https://www.okx.com'
OKX_POSITION_ENDPOINT = '/api/v5/account/positions'
OKX_BALANCE_ENDPOINT = '/api/v5/account/balance'

BITGET_BASE_URL = 'https://api.bitget.com'
BITGET_ORDER_ENDPOINT = '/api/mix/v1/order/placeOrder'
BITGET_BALANCE_ENDPOINT = '/api/mix/v1/account/accounts'

def get_okx_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def get_bitget_timestamp():
    return str(int(time.time() * 1000))

def generate_okx_signature(timestamp, method, request_path, body):
    message = timestamp + method + request_path + (body or '')
    mac = hmac.new(OKX_API_SECRET.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def generate_bitget_signature(timestamp, method, request_path, body):
    message = timestamp + method + request_path + (body or '')
    mac = hmac.new(BITGET_API_SECRET.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def get_okx_positions():
    timestamp = get_okx_timestamp()
    headers = {
        'OK-ACCESS-KEY': OKX_API_KEY,
        'OK-ACCESS-SIGN': generate_okx_signature(timestamp, 'GET', OKX_POSITION_ENDPOINT, ''),
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': OKX_API_PASS,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(OKX_BASE_URL + OKX_POSITION_ENDPOINT, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching OKX positions: {response.status_code}")
        print(response.text)
        return None

def get_okx_balance():
    timestamp = get_okx_timestamp()
    headers = {
        'OK-ACCESS-KEY': OKX_API_KEY,
        'OK-ACCESS-SIGN': generate_okx_signature(timestamp, 'GET', OKX_BALANCE_ENDPOINT, ''),
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': OKX_API_PASS,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(OKX_BASE_URL + OKX_BALANCE_ENDPOINT, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching OKX balance: {response.status_code}")
        print(response.text)
        return None

def get_bitget_balance():
    timestamp = get_bitget_timestamp()
    endpoint = BITGET_BALANCE_ENDPOINT + '?productType=umcbl'
    headers = {
        'ACCESS-KEY': BITGET_API_KEY,
        'ACCESS-SIGN': generate_bitget_signature(timestamp, 'GET', endpoint, ''),
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': BITGET_API_PASS,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(BITGET_BASE_URL + endpoint, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching Bitget balance: {response.status_code}")
        print(response.text)
        return None

def save_positions_to_json(positions, filename='okx_positions.json'):
    with open(filename, 'w') as f:
        json.dump(positions, f, indent=4)

def load_positions_from_json(filename='okx_positions.json'):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump({"data": []}, f)
    
    with open(filename, 'r') as f:
        return json.load(f)

def convert_symbol(okx_symbol):
    return okx_symbol.replace("-SWAP", "")

def convert_okx_to_bitget_position(okx_position, action='open', quantity_ratio=1.0):
    bitget_position = {
        "symbol": convert_symbol(okx_position["instId"]),
        "side": "open_long" if okx_position["posSide"] == "long" else "open_short",
        "leverage": okx_position["lever"],
        "quantity": str(float(okx_position["pos"]) * quantity_ratio),
        "orderType": "market",
        "marginMode": "cross",
        "price": "",  # Market order doesn't require price
        "clientOrderId": "",  # Optional, can be used for tracking orders
        "reduceOnly": action == 'close'
    }
    return bitget_position

def place_bitget_order(bitget_position):
    timestamp = get_bitget_timestamp()
    headers = {
        'ACCESS-KEY': BITGET_API_KEY,
        'ACCESS-SIGN': generate_bitget_signature(timestamp, 'POST', BITGET_ORDER_ENDPOINT, json.dumps(bitget_position)),
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': BITGET_API_PASS,
        'Content-Type': 'application/json'
    }
    
    response = requests.post(BITGET_BASE_URL + BITGET_ORDER_ENDPOINT, headers=headers, data=json.dumps(bitget_position))
    
    if response.status_code == 200:
        print("Order placed successfully on Bitget")
    else:
        print(f"Error placing order on Bitget: {response.status_code}")
        print(response.text)

def compare_and_sync_positions(prev_positions, current_positions, quantity_ratio):
    prev_positions_dict = {pos['instId']: pos for pos in prev_positions['data']}
    current_positions_dict = {pos['instId']: pos for pos in current_positions['data']}
    
    # Check for new or increased positions
    for instId, current_pos in current_positions_dict.items():
        prev_pos = prev_positions_dict.get(instId)
        if not prev_pos:
            # New position
            bitget_position = convert_okx_to_bitget_position(current_pos, action='open', quantity_ratio=quantity_ratio)
            place_bitget_order(bitget_position)
        elif float(current_pos['pos']) > float(prev_pos['pos']):
            # Increased position
            bitget_position = convert_okx_to_bitget_position(current_pos, action='open', quantity_ratio=quantity_ratio)
            place_bitget_order(bitget_position)
    
    # Check for decreased or closed positions
    for instId, prev_pos in prev_positions_dict.items():
        current_pos = current_positions_dict.get(instId)
        if not current_pos:
            # Closed position
            bitget_position = convert_okx_to_bitget_position(prev_pos, action='close', quantity_ratio=quantity_ratio)
            place_bitget_order(bitget_position)
        elif float(current_pos['pos']) < float(prev_pos['pos']):
            # Decreased position
            bitget_position = convert_okx_to_bitget_position(prev_pos, action='close', quantity_ratio=quantity_ratio)
            bitget_position['quantity'] = str(float(prev_pos['pos']) - float(current_pos['pos']) * quantity_ratio)
            place_bitget_order(bitget_position)

def sync_positions():
    prev_positions = load_positions_from_json()
    current_positions = get_okx_positions()

    okx_balance = get_okx_balance()
    bitget_balance = get_bitget_balance()
    
    if okx_balance and bitget_balance:
        okx_equity = float(okx_balance['data'][0]['details'][0]['eq'])
        bitget_equity = float(bitget_balance['data'][0]['usdtEquity'])
        quantity_ratio = bitget_equity / okx_equity if okx_equity != 0 else 1.0
        print(f"Quantity ratio: {quantity_ratio}")

        if current_positions:
            save_positions_to_json(current_positions)
            compare_and_sync_positions(prev_positions, current_positions, quantity_ratio)

def signal_handler(sig, frame):
    print('\nProgram interrupted. Exiting gracefully...')
    exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        while True:
            sync_positions()
            time.sleep(3)  # Check every 3 seconds
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)
