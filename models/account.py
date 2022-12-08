from audioop import add
from email import message
import imp
from locale import currency
from unicodedata import decimal
from flask import jsonify
from helpers.dbhelper import Database as Db
from helpers.modal import Modal as Md
from application import web3
import requests
from config import config as cfg
import json
import os


class Account:
    def __init__(self):
        self.wallet = ""

    def to_wei(self, amount):
        return amount * self.precision

    def from_wei(self, amount):
        return amount / self.precision

    def generate_keypair(self):
        account = web3.eth.account.create()
        decoded_hash = account.key.hex()
        response = {
            "address": account.address,
            "privateKey": decoded_hash
        }
        return response

    def make_transfer(self, rq):
        try:
            data = rq.json
            print("transaction request received")
            print(data)
            amount = data['amount']
            recipient = data['recipient']
            address = data['address']
            secret_key = os.getenv("pay_account_private_key")
            extra_data = data['extra_data']
            sending_token = data['sending_token']
            service_id = extra_data['service_id']
            account_number = extra_data['account_number']
            currency = os.getenv("currency")
            contract = Md().get_contract(currency)
            
            abi = contract[0]
            contract = contract[1]
            contract_address = contract['contract_address']
            decimals = contract['decimals']
            
            service_info = get_service(service_id)
            print(service_info)

            if amount <= 0:
                return Md.make_response(404, "invalid amount")

            if len(service_info) == 0:
                print("service not found")
                return Md.make_response(404, "service not found")

            merchant_celo_address = service_info['address']
            if recipient != merchant_celo_address:
                return Md.make_response(404, "sent recipient address does not match receiver address")

            amount_to_send = int(amount) * int(decimals)
            print(amount_to_send)

            unicorns = web3.eth.contract(address=contract_address, abi=abi)
            print(unicorns.address)

            sender_account = web3.eth.account.privateKeyToAccount(secret_key)

            sender_address = sender_account.address
            #sender_address = address
            print(sender_address)

            gasPrice = web3.toWei(cfg["gasPrice"], 'gwei')

            transaction = unicorns.functions.transfer(
                recipient,
                amount_to_send
            ).buildTransaction({
                'gas': int(cfg["gas"]),
                'nonce': web3.eth.getTransactionCount(sender_address),
                'gasPrice': gasPrice,
                'chainId': int(cfg["chain_id"])
            })
            print(transaction)
            signed_tx = web3.eth.account.signTransaction(
                transaction, secret_key)
            tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            decoded_hash = tx_hash.hex()
            print("transaction sent, ", decoded_hash)
            message = {"txHash": decoded_hash,
                       "currency": os.getenv("coin"),
                       "amount": amount,
                       "contract_address": contract_address
                       }
            return Md.make_response(100, message)

        except Exception as e:
            print(e)
            return Md.make_response(203, "transaction failed " + str(e))
    

    def get_linked_address(self,):
        try:
            secret_key = os.getenv("pay_account_private_key")
            sender_account = web3.eth.account.privateKeyToAccount(secret_key)
            address = sender_account.address
            return jsonify({"address": address}), 200
        except Exception as e:
            print(e)
            return Md.make_response(203, str(e))

    def get_env_balance(self,):
        try:
            secret_key = os.getenv("pay_account_private_key")
            sender_account = web3.eth.account.privateKeyToAccount(secret_key)
            address = sender_account.address
            unicorns = web3.eth.contract(
                address=self.contract_address, abi=self.abi)
            balance = unicorns.functions.balanceOf(address).call()
            bl = {
                "balance": web3.fromWei(balance, 'gwei'),
                "asset": os.getenv("coin"),
                "contract_address": os.getenv("cugx_contract_address")
            }

            return jsonify(bl), 200

            account = web3.eth.get_balance(address)
            print(account)
            balance_list = dict()
            for key in account:
                balance_value = self.from_wei(account[key])
                balance_list[key] = balance_value
            balance_list[self.token_code] = balance
            return jsonify(balance_list)
        except Exception as e:
            print(e)
            return Md.make_response(203, str(e))

    def get_account_balance(self, address):
        try:
            unicorns = web3.eth.contract(
                address=self.contract_address, abi=self.abi)
            balance = unicorns.functions.balanceOf(address).call()

            account = web3.get_total_balance(address)
            balance_list = dict()
            for key in account:
                balance_value = self.from_wei(account[key])
                balance_list[key] = balance_value
            balance_list[self.token_code] = balance
            return jsonify(balance_list)
        except Exception as e:
            print(e)
            return Md.make_response(203, str(e))

    def make_transfer_uxg_contract(self, rq):
        # TODO: ADD THE cUGX CONTRACT TRANSACTIONS
        try:
            ugx_contract = "0x0156308E8fC5763F31afCc2153a387cdEEFd5ecF"
            ABI = ""
            contract_info = web3.eth.contract(ugx_contract)
            function = contract_info.functions.name().call()
            print(function)

        except Exception as e:
            print(e)


def get_service(service_id):
    url = "https://muda-dev.github.io/Liqudity-Rail/services.json"
    response = requests.request("GET", url)
    data = response.json()
    for x in data:
        print(x["service_id"])
        if x['service_id'] == service_id:
            return x
    return []


def log_transaction(decoded_hash, recipient, amount, sending_token, extra_data):
    # save txn to local db
    return True


def auth_user(username, password):
    values = {"username": username, "password": password}
    data = Db.select("sia_user", "*", **values)
    return data
