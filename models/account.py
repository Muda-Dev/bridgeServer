from flask import jsonify
import os
import requests

from helpers.XRPLedger import XRPLedger
from helpers.dbhelper import Database as Db
from helpers.modal import Modal as Md
from helpers.config import service_url
from abc import ABC, abstractmethod
from helpers.XRPLedger import XRPLedger
from helpers.EVMConnector import EVMConnector

xrp = XRPLedger()


class Chain(ABC):
    @abstractmethod
    def generate_keypair(self):
        pass

    @abstractmethod
    def get_balance(self, address):
        pass

    @abstractmethod
    def get_transaction(self, hash):
        pass


class EVMChain(Chain):
    def __init__(self):
        self.evm = EVMConnector()

    def generate_keypair(self):
        return self.evm.generate_keypair()

    def get_balance(self, address):
        return self.evm.get_total_balance(address)

    def get_transaction(self, hash):
        return self.evm.get_transaction_by_hash(hash)


class XRPChain(Chain):
    def __init__(self):
        self.xrp = XRPLedger()
        self.evm = EVMConnector(os.getenv("CONTRACT_ADDRESS"),abi=os.getenv("ABI"),rpc_url=os.getenv("RPC"),chain_id=1)

    def generate_keypair(self):
        classic_address, seed = self.xrp.generate_key_pair()
        return {
            "classic_address": classic_address,
            "seed": seed
        }

    def get_balance(self, address):
        return self.xrp.check_balance(address)

    def get_transaction(self, hash):
        return self.xrp.get_single_transaction(hash)


class ChainFactory:
    def get_chain(self, chain_name):
        chains = {
            'EVM': EVMChain,
            'XRP': XRPChain
        }

        chain = chains.get(chain_name.upper())
        if not chain:
            raise ValueError('Invalid chain name')
        return chain()


class Account:
    def __init__(self):
        self.chain_factory = ChainFactory()
        self.wallet = ""

    def generate_keypair(self, request):
        data = request.json
        chain = data['chain']
        chain_instance = self.chain_factory.get_chain(chain)
        print(chain_instance)
        return chain_instance.generate_keypair()

    def check_balance(self, request):
        data = request.json
        chain = data['chain']
        address = data['address']
        chain_instance = self.chain_factory.get_chain(chain)
        return chain_instance.get_balance(address)

    def get_transaction(self, request):
        data = request.json
        chain = data['chain']
        tx_hash = data['hash']
        chain_instance = self.chain_factory.get_chain(chain)
        return chain_instance.get_transaction(tx_hash)


    def make_transfer(self, request):
        try:
            data = request.json
            amount = float(data['amount'])
            recipient = str(data['recipient'])
            extra_data = data.get('extra_data', {})
            service_id = extra_data.get('service_id', "")
            chain = extra_data.get('chain', "")
            currency = str(data['currency'])

            if not amount or amount <= 0:
                return Md.make_response(404, "invalid amount")

            service_info = get_service(service_id, chain)
            merchant_address = service_info.get('address', "")

            if not service_info:
                return Md.make_response(404, "service not found")

            if recipient != merchant_address:
                return Md.make_response(404, "sent recipient address does not match receiver address")

            if chain == "XRP":
                hash_value = Account.handle_xrp_transfer(
                    amount, merchant_address, data)
            else:  # Assuming this means EVM
                hash_value = Account.handle_evm_transfer(self,
                    amount, merchant_address, data)

            return Account.log_transaction(hash_value, service_id, chain, currency, amount, recipient, data)

        except Exception as e:
            return Md.make_response(203, "transaction failed " + str(e))

    @staticmethod
    def handle_evm_transfer(self, amount, merchant_address, data):
        gas_price = data.get('gas_price', 0)
        chain_id = data.get('chain_id', 0)

        # assuming amount is in ETH for native coin transfer
        hash_value = self.evm.make_native_coin_transfer(
            Account.SECRET_KEY, merchant_address, amount, gas_price, chain_id)

        return hash_value

    @staticmethod
    def create_account(request):
        data = request.json
        sender_address = data['sender_address']
        sender_secret = data['sender_secret']
        new_account_address = data['new_account_address']
        amount = data['amount']  # Should be at least 20 XRP (20000000 drops)
        response = xrp.create_account(
            sender_address, sender_secret, new_account_address, amount)
        return response

    @staticmethod
    def check_balance(request):
        data = request.json
        address = data['address']
        balance = xrp.check_balance(address)
        return balance

    @staticmethod
    def get_transaction(request):
        data = request.json
        hash = data['hash']
        transaction = xrp.get_single_transaction(hash)
        return transaction

    @staticmethod
    def fund_account(request):
        data = request.json
        sender_address = data['sender_address']
        sender_secret = data['sender_secret']
        recipient_address = data['recipient_address']
        amount = data['amount']
        response = xrp.fund_account(
            sender_address, sender_secret, recipient_address, amount)
        return response

    @staticmethod
    def make_path_payment(request):
        data = request.json
        sender_address = data['sender_address']
        sender_secret = data['sender_secret']
        recipient_address = data['recipient_address']
        source_currency = data['source_currency']
        source_issuer = data['source_issuer']
        source_amount = data['source_amount']
        destination_currency = data['destination_currency']
        destination_issuer = data['destination_issuer']
        destination_amount = data['destination_amount']
        response = xrp.make_path_payment(
            sender_address, sender_secret, recipient_address,
            source_currency, source_issuer, source_amount,
            destination_currency, destination_issuer, destination_amount
        )
        return response

    @staticmethod
    def log_transaction(hash_value, service_id, chain, currency, amount, recipient, data):
        sql = {
            "transaction_id": hash_value,
            "service_id": service_id,
            "chain": chain,
            "account_number": data['extra_data']['account_number'],
            "status": "PENDING",
            "currency": currency,
            "amount": amount,
            "thirdparty_transaction_id": "",
            "source": "sender_address",
            "destination": recipient,
            "request_obj": data
        }
        Db().insert("SentTransaction", **sql)

        message = {
            "txHash": hash_value,
            "currency": os.getenv("coin"),
            "amount": data['amount']
        }
        return Md.make_response(100, message)


def get_service(service_id, chain):
    url = service_url
    response = requests.request("GET", url)
    data = response.json()
    for x in data:
        if x.get('service_id') == service_id and x.get('chain')==chain:
            return x
    return {}
