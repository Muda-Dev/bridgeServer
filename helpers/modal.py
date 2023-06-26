import json
from unicodedata import decimal
import jwt
from flask import jsonify, request
from cryptography.fernet import Fernet
import os
import urllib3
import requests
from helpers.contracts import config as cfg


class Modal:

    def __init__(self):
        self.app_key = os.getenv("enc_key")

    def encrypt_info(self, message):
        fernet = Fernet(self.app_key)
        encMessage = fernet.encrypt(message.encode()).decode()
        return encMessage

    def decrypt_info(self, encMessage):
        fernet = Fernet(self.app_key)
        decMessage = fernet.decrypt(encMessage.encode()).decode()
        return decMessage

    @staticmethod
    def make_response(status, message, data=None):
        if data is None:
            rsp = {'status': status, 'message': message}
        else:
            rsp = {'status': status, 'message': message, "data": data}
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
                contract = cfg['cugx_contract']
            elif coin == "usd":
                contract = cfg['cusd_contract']
            coin_abi = contract['abi']
            abi = coin_abi
            coin = [abi, contract]
            return coin
        except Exception as e:
            print(e)
            return ""

    @staticmethod
    def send_post_request(data, url):
        payload = json.dumps(data)
        headers = {
            'Content-Type': 'application/json'
        }
        print("payload", payload)
        response = requests.request("POST", url, headers=headers, data=payload)
        return response

    @staticmethod
    def file_get_contents(url):
        try:
            url = str(url).replace(" ", "+")  # just in case, no space in url
            http = urllib3.PoolManager()
            r = http.request('GET', url)
            # r.status
            print(r.data)
            return True
        except Exception as e:
            print(e)
        return ''


def token_required(f):
    return True
