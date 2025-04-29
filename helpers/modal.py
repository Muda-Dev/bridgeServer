import json
import os
import requests
import urllib3
from flask import jsonify
from cryptography.fernet import Fernet
from helpers.dbhelper import Database as Db
from dotenv import load_dotenv

load_dotenv()

RAIL_URL = "https://rail.stage-mudax.xyz/accounts/"

class Modal:
    def __init__(self):
        self.app_key = os.getenv("enc_key")
        self.coin_market = os.getenv("COIN_MARKET")
        self.rate_endpoint = os.getenv("RATE_ENDPOINT")

    def encrypt_info(self, message: str) -> str:
        fernet = Fernet(self.app_key)
        return fernet.encrypt(message.encode()).decode()

    def decrypt_info(self, enc_message: str) -> str:
        fernet = Fernet(self.app_key)
        return fernet.decrypt(enc_message.encode()).decode()

    @staticmethod
    def make_response(status: int, message: str, data=None):
        response = {"status": status, "message": message}
        if data is not None:
            response["data"] = data

        # Map internal status codes to HTTP status codes.
        if status == 100:
            code = 200
        elif status == 404:
            code = 404
        else:
            code = 403

        return jsonify(response), code

    def get_contract(self, coin: str):
        # Note: 'cfg' must be defined elsewhere in your project.
        try:
            contract = ""
            coin = coin.lower()
            if coin == "ugx":
                contract = cfg["cugx_contract"]
            elif coin == "usd":
                contract = cfg["cusd_contract"]

            coin_abi = contract.get("abi", {})
            return [coin_abi, contract]
        except Exception as e:
            print("Error in get_contract:", e)
            return ""

    def get_service(self, service_id, chain):
        url = "service_url"  # Replace with the actual service URL.
        try:
            response = requests.get(url)
            data = response.json()
            for entry in data:
                if entry.get("service_id") == service_id:
                    return entry
        except Exception as e:
            print("Error in get_service:", e)
        return {}


    def process_pending_transactions(self):
        try:
            condition = "transaction_status IN ('PENDING', 'INITIATED')"
            pending_transactions = Db().select("receivedTransactions", condition)
            for transaction in pending_transactions:
                transaction_id = transaction.get("quote_id")
                if transaction_id:
                    self.get_transaction_status(transaction_id)
        except Exception as e:
            print("Error in process_pending_transactions:", e)

    def get_transaction_status(self, transaction_id):
        try:
            status_url = os.getenv("STATUS_URL")
            payload = {"quote_id": transaction_id}
            headers = {"Content-Type": "application/json"}
            response = requests.post(status_url, headers=headers, data=json.dumps(payload))
            response_data = response.json()

            if response.status_code == 200:
                update_transaction(transaction_id, "SUCCESSFUL")
                return {"status": "success", "message": "Payout successful"}
            elif response.status_code == 201:
                update_transaction(transaction_id, "INITIATED", response_data.get("message"))
                return {"status": "initiated", "message": "Payout started"}
            else:
                update_transaction(transaction_id, "FAILED", response_data.get("message"))
                return {"status": "error", "message": "Payout failed"}
        except Exception as e:
            print("Error in get_transaction_status:", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_post_request(data, url):
        payload = json.dumps(data)
        headers = {"Content-Type": "application/json"}
        print("Sending POST request with payload:", payload)
        return requests.post(url, headers=headers, data=payload)

    @staticmethod
    def file_get_contents(url):
        try:
            safe_url = str(url).replace(" ", "+")
            http = urllib3.PoolManager()
            r = http.request("GET", safe_url)
            print("File contents:", r.data)
            return r.data
        except Exception as e:
            print("Error in file_get_contents:", e)
            return ""



    @staticmethod
    def payout_callback(callback_id, receiver_address, sending_address, asset_amount, asset_code, asset_issuer, chain,memo):
        """
        Processes a payout callback by:
        1. Validating the asset amount.
        2. Calculating the payout amount.
        3. Fetching quote data.
        4. Composing the unified payload from the quote data and additional payout fields.
        5. Logging and sending the payout request.
        6. Updating the transaction based on the payout service response.
        """
        # Ensure asset code is uppercase.
        asset_code = asset_code.upper()
        payout_currency = os.getenv("PAY_CURRENCY")

        
        try:
            asset_amount = float(asset_amount)
        except ValueError:
            print("Invalid asset amount")
            return {"status": "error", "message": "Invalid asset amount"}
        
        print(f"Payout callback: sending_address={sending_address}, amount={asset_amount}, asset_code={asset_code}")
        
        # Calculate the payout amount.
        payout_amount = make_exchange(asset_amount, asset_code, payout_currency)
        
        # Fetch the quote data.
        quote_response = get_quote_data(payout_currency, receiver_address, sending_address, asset_code, asset_amount, chain,memo)
        if not quote_response:
            update_log(callback_id, "Failed to fetch quote data")
            return {"status": "error", "message": "Failed to fetch quote data"}
        
        # Check the quote service status.
        if quote_response.get("status") != 200:
            update_log(callback_id, f"Quote service error: {quote_response.get('message')}")
            return {"status": "error", "message": "Quote service error"}
        
        # Extract data from the quote response.
        quote_data = quote_response.get("data", {})
        transaction_id = quote_data.get("transId")
        hash_value = quote_data.get("id")
        service_id = quote_data.get("service_id")
        account_number = quote_data.get("account_number")
        rate = quote_data.get("rate", 1)
        
        # Optional: Insert quote record into the database.
        sql = {
            "quote_id": transaction_id,
            "hash": callback_id,
            "sending_address": sending_address,
            "receiver_address": receiver_address,
            "internal_transaction_id": "",  # No internal transaction provided.
            "service_id": service_id,
            "account_number": account_number,
            "received_asset": quote_data.get("send_asset"),
            "received_amount":asset_amount,
            "payout_currency": quote_data.get("receive_currency"),
            "trans_type": "BANK",
            "payout_amount":payout_amount,
            "status": quote_data.get("status")
        }
        result = Db().insert("receivedTransactions", **sql)
        print("Inserted quote record:", result)
        hook_response = send_webhook_update(transaction_id, callback_id, "SUCCESSFUL", "CHAIN_RECEIVED")
        print("HOOK_RESPONSE",hook_response)
        if not hook_response or hook_response.get("status") != 200:
            return False
  
        # Compose the final payload using the quote data and additional payout details.
        unified_payload = {
            "transId": transaction_id,
            "service_id": service_id,
            "quote_id": hash_value,
            "receivedAsset": quote_data.get("send_asset"),
            "receivedAmount": asset_amount,
            "payOutCurrency": quote_data.get("receive_currency"),
            "payoutAmount": round(payout_amount),
            "chainInfo": {
                "asset_amount": asset_amount,
                "asset_code": asset_code,
                "to_address": receiver_address,
                "from_address": sending_address,
                "chain": chain, 
                "contract_address": asset_issuer,
                "hash": hash_value
            },
            "accountInfo": {
                "account_type": "BANK",  # Update as needed.
                "account_name": "",        # Update if available.
                "account_number": account_number
            }
        }
        
        # Serialize the payload.
        payload_json = json.dumps(unified_payload)
        
        # Log the payout request.
        save_log(callback_id, asset_code, asset_amount, asset_issuer, payload_json)
        
        payout_url = os.getenv("PAYOUT_URL")
        headers = {"Content-Type": "application/json"}
        print("Sending payout request to", payout_url, payload_json)
        
        try:
            response = requests.post(payout_url, headers=headers, data=payload_json)
            response_data = response.json()
            print(f"Payout Response: Status {response.status_code}, Body: {response.text}")
            update_log(callback_id, json.dumps(response_data))
        except Exception as e:
            update_log(callback_id, str(e))
            return {"status": "error", "message": "Payout request failed"}
        
        # Update transaction status based on the response.
        
        if response_data.get("status")  == 200:
            update_transaction(transaction_id, "SUCCESSFUL")
            return {"status": "success", "message": "Payout successful"}
        elif response_data.get("status") == 201:
            update_transaction(transaction_id, "INITIATED", response_data.get("message"))
            return {"status": "initiated", "message": "Payout started"}
        else:
            update_transaction(transaction_id, "FAILED", response_data.get("message"))
            return {"status": "error", "message": "Payout failed"}

def get_quote_data(receive_currency, receiver_address, sending_address, send_asset, send_amount, chain,memo):
    """
    Fetches the quote data from the quote service and returns the raw JSON response.
    """
    try:
        payload = {
            "receive_currency": receive_currency,
            "receiver_address": receiver_address,
            "sending_address": sending_address,
            "send_asset": send_asset,
            "status": "PENDING",
            "memo":memo,
            "send_amount": send_amount
        }
        payload_json = json.dumps(payload)
        quote_url = os.getenv("QUOTE_URL", RAIL_URL+"queryQuote")
        headers = {"Content-Type": "application/json"}
        print("Sending quote request to", quote_url, "with payload", payload_json)
        
        response = requests.post(quote_url, headers=headers, data=payload_json)
        return response.json()
    except Exception as e:
        print("Error in fetching quote data:", e)
        return None

        
def send_webhook_update(trans_id, hash_value, status, event_type):
    try:
        payload = {
            "transId": trans_id,
            "hash": hash_value,
            "status": status,
            "event_type": event_type
        }
        payload_json = json.dumps(payload)
        webhook_url = os.getenv("WEBHOOK_URL", RAIL_URL+"callback")
        headers = {"Content-Type": "application/json"}
        print("Sending webhook update to", webhook_url, "with payload", payload_json)
        
        response = requests.post(webhook_url, headers=headers, data=payload_json)
        print("Sending webhook response", response.json())
        return response.json()
    except Exception as e:
        print("Error in sending webhook update:", e)
        return None

def make_exchange(amount, symbol="BTC", convert="USD"):
    print(f"make_exchange called with amount={amount}, symbol={symbol}, convert={convert}")
    response_data = get_exchange_rates(amount, symbol, convert)
    print("Exchange rate response:", response_data)
    if response_data.get("status") != 200:
        print("Exchange rate error:", response_data.get("message"))
        return 0
    return response_data.get("converted_amount", 0)


def fetch_from_custom_endpoint(amount, symbol, convert):
    response = requests.get(
        os.getenv("RATE_ENDPOINT"),
        headers={"Accepts": "application/json"},
        params={"amount": amount, "symbol": symbol, "convert": convert},
    )
    if response.status_code == 200:
        data = response.json()
        converted_amount = amount * data.get("rate", 0)
        return {"status": 200, "converted_amount": converted_amount}
    else:
        return {"status": response.status_code, "message": "Failed to fetch from custom endpoint"}


def get_exchange_rates(amount, symbol="BTC", convert="USD"):
    url = os.getenv("RATE_ENDPOINT")
    if symbol == "CNGN":
        symbol = "NGN"

    request_data = {"from": symbol, "to": convert}
    payload_json = json.dumps(request_data)
    print("Exchange request to", url, "with data", request_data)
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=payload_json)
    print(f"Exchange response: Status {response.status_code}, Body: {response.text}")

    if response.status_code == 201:
        data = response.json()
        price_info = data.get("response", {}).get("rate")
        print("Price info:", price_info)
        try:
            converted_amount = round(float(amount) * float(price_info), 2)
            return {"status": 200, "converted_amount": converted_amount}
        except Exception as e:
            print("Error calculating converted amount:", e)
            return {"status": 500, "message": "Calculation error"}
    else:
        return {"status": response.status_code, "message": "Failed to fetch from custom endpoint"}


def get_exchange_rates_coin(amount, symbol="BTC", convert="USD"):
    response = requests.get(
        "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
        headers={
            "X-CMC_PRO_API_KEY": os.getenv("COIN_MARKET"),
            "Accepts": "application/json",
        },
        params={"symbol": symbol, "convert": convert},
    )
    if response.status_code == 200:
        data = response.json()
        price_info = (
            data.get("data", {})
            .get(symbol, {})
            .get("quote", {})
            .get(convert, {})
            .get("price")
        )
        converted_amount = amount * price_info if price_info else 0
        return {"status": 200, "converted_amount": converted_amount}
    else:
        return {"status": response.status_code, "message": "Failed to fetch from CoinMarketCap"}

def update_transaction(id, status, reason=None):
    if status not in ['PENDING', 'FAILED', 'SUCCESSFUL', 'INITIATED']:
        print("Invalid status:", status)
        return False

    try:
        sql = {"status": status, "reason": reason}
        condition = f"quote_id='{id}'"
        print("UPDATE_", condition, sql)
        result = Db().Update("receivedTransactions", condition, **sql)
        print("Transaction update result:", result)
        send_webhook_update(id, "", status, "PAYOUT")
        return True
    except Exception as e:
        print("Error in update_transaction:", e)
        return False


def save_log(hash_value, asset_code, asset_amount, asset_issuer, data):
    try:
        sql = {
            "hash": hash_value,
            "received_asset": asset_code,
            "amount": asset_amount,
            "contract_address": asset_issuer,
            "req_body": data
        }
        result = Db().insert("pay_log", **sql)
        print("Log saved:", result)
        return True
    except Exception as e:
        print("Error in save_log:", e)
        return False


def update_log(hash_value, data):
    try:
        sql = {"resp_body": data}
        condition = f"hash='{hash_value}'"
        result = Db().Update("pay_log", condition, **sql)
        print("Log update result:", result)
        return True
    except Exception as e:
        print("Error in update_log:", e)
        return False


def token_required(f):
    # Placeholder decorator for token authentication.
    return f
