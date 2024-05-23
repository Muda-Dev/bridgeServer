import json
import os
import requests
from flask import jsonify
from cryptography.fernet import Fernet


class Modal:
    def __init__(self):
        self.app_key = os.getenv("enc_key")
        self.coin_market = os.getenv("COIN_MARKET")
        self.rate_endpoint = os.getenv("RATE_ENDPOINT")

    def encrypt_info(self, message):
        fernet = Fernet(self.app_key)
        return fernet.encrypt(message.encode()).decode()

    def decrypt_info(self, encMessage):
        fernet = Fernet(self.app_key)
        return fernet.decrypt(encMessage.encode()).decode()


    @staticmethod
    def make_response(status, message, data=None):
        if data is None:
            rsp = {"status": status, "message": message}
        else:
            rsp = {"status": status, "message": message, "data": data}
        if status == 100:
            code = 200
        elif status == 404:
            code = 404
        else:
            code = 403
        return jsonify(rsp), code

    def get_contract(self, coin):
        try:
            contract = ""
            if coin == "ugx":
                contract = cfg["cugx_contract"]
            elif coin == "usd":
                contract = cfg["cusd_contract"]
            coin_abi = contract["abi"]
            abi = coin_abi
            coin = [abi, contract]
            return coin
        except Exception as e:
            print(e)
            return ""

    def get_service(self, service_id, chain):
        url = "service_url"
        response = requests.get(url)
        data = response.json()
        for entry in data:
            if entry.get("service_id") == service_id:
                return entry
        return {}


    @staticmethod
    def payout_callback(
        id, address, transId, asset_amount, asset_code, asset_issuer, chain
    ):
        asset_code = asset_code.upper()
        currency = "UGX"
        asset_amount = float(asset_amount)

        print({transId, asset_amount, asset_code})
        payout_amount = make_exchange(asset_amount, asset_code, currency)
        if not payout_amount:
            # Handling cases where exchange rate couldn't be fetched or calculation failed
            print("Failed to calculate payout amount.")
            return None

        payload = {
            "hash": id,
            "transId":transId,
            "payout_amount":round(payout_amount),
            "asset_amount":asset_amount,
            "asset_code":asset_code,
            "contract_address":asset_issuer,
            "chain":chain
        }

        # Convert payload to JSON
        payload_json = json.dumps(payload)
        payout_url = os.getenv("PAYOUT_URL")
        headers = {"Content-Type": "application/json"}
        print("sending request to ",payout_url, payload_json)

        response = requests.post(payout_url, headers=headers, data=payload_json)

        # Log the response for debugging purposes
        print(f"Webhook Response Status: {response.status_code}, Body: {response.text}")

        return response

    # Assuming other methods remain unchanged...

    @staticmethod
    def send_post_request(data, url):
        payload = json.dumps(data)
        headers = {"Content-Type": "application/json"}
        print("payload", payload)
        response = requests.request("POST", url, headers=headers, data=payload)
        return response

    @staticmethod
    def file_get_contents(url):
        try:
            url = str(url).replace(" ", "+")  # just in case, no space in url
            http = urllib3.PoolManager()
            r = http.request("GET", url)
            # r.status
            print(r.data)
            return True
        except Exception as e:
            print(e)
        return ""


def make_exchange(amount, symbol="BTC", convert="USD"):
    """Fetches the exchange rate and calculates the converted amount, returns only the converted amount."""
    # Check if a custom rate endpoint is provided
    if os.getenv("RATE_ENDPOINT") !="":
        response_data = fetch_from_custom_endpoint(amount, symbol, convert)
    else:
        response_data = get_exchange_rates(amount, symbol, convert)

    # Check for errors in the response
    print("exrate", response_data)
    if "status" in response_data and response_data["status"] != 200:
        print("exchage rate error, ", response_data["message"])
        return 0
    return response_data["converted_amount"]

def fetch_from_custom_endpoint(amount, symbol, convert):
    """Fetches exchange rates from a custom endpoint and returns the structured response."""
    response = requests.get(
        os.getenv("RATE_ENDPOINT") ,
        headers={"Accepts": "application/json"},
        params={"amount": amount, "symbol": symbol, "convert": convert},
    )
    if response.status_code == 200:
        data = response.json()
        # Calculate converted amount using rate from custom endpoint's response
        converted_amount = amount * data["rate"]
        return {"status": 200, "converted_amount": converted_amount}
    else:
        return {
            "status": response.status_code,
            "message": "Failed to fetch from custom endpoint",
        }

def get_exchange_rates(amount, symbol="BTC", convert="USD"):
    """Fetches exchange rates from CoinMarketCap, calculates converted amount, and returns structured response."""
    response = requests.get(
        "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
        headers={
            "X-CMC_PRO_API_KEY": os.getenv("COIN_MARKET") ,
            "Accepts": "application/json",
        },
        params={"symbol": symbol, "convert": convert},
    )
    if response.status_code == 200:
        data = response.json()
        price_info = data["data"][symbol]["quote"][convert]["price"]
        converted_amount = amount * price_info
        return {"status": 200, "converted_amount": converted_amount}
    else:
        return {
            "status": response.status_code,
            "message": "Failed to fetch from CoinMarketCap",
        }


def token_required(f):
    return True
