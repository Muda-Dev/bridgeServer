from flask import jsonify
import os
import requests

from application import web3
from helpers.XRPLedger import XRPLedger
from helpers.contracts import config as cfg
from helpers.dbhelper import Database as Db
from helpers.modal import Modal as Md
from helpers.EVMConnector import EVMConnector
from helpers.config import service_url

xrp = XRPLedger()
connector = EVMConnector()


class Account:
    def __init__(self):
        self.wallet = ""

    @staticmethod
    def to_wei(amount):
        return amount * cfg["precision"]

    @staticmethod
    def from_wei(amount):
        return amount / cfg["precision"]

    @staticmethod
    def generate_keypair():
        keypairs = []

        # Generate key pair for Ethereum (EVM)
        account = web3.eth.account.create()
        decoded_hash = account.key.hex()
        evm_keypair = {
            "address": account.address,
            "privateKey": decoded_hash
        }
        keypairs.append({"EVM": evm_keypair})

        # Generate key pair for XRP
        classic_address, seed = xrp.generate_key_pair()
        xrp_keypair = {
            "classic_address": classic_address,
            "seed": seed
        }
        keypairs.append({"XRP": xrp_keypair})
        return keypairs

    @staticmethod
    def make_transfer(request):
        try:
            data = request.json
            amount = data['amount']
            recipient = data['recipient']
            extra_data = data['extra_data']
            service_id = extra_data['service_id']
            chain = extra_data['chain']
            currency = data['currency']

            if amount <= 0:
                return Md.make_response(404, "invalid amount")

            service_info = get_service(service_id, chain)
            merchant_address = service_info['address']

            if not service_info:
                return Md.make_response(404, "service not found")

            if recipient != merchant_address:
                return Md.make_response(404, "sent recipient address does not match receiver address")

            if chain == "XRP":
                hash_value = Account.handle_xrp_transfer(
                    amount, merchant_address, data)
            else:
                hash_value, contract_address, amount_to_send = Account.handle_evm_transfer(
                    amount, recipient, currency, data)

            return Account.log_transaction(hash_value, service_id, chain, currency, amount_to_send, recipient, data, contract_address)

        except Exception as e:
            return Md.make_response(203, "transaction failed " + str(e))

    @staticmethod
    def handle_xrp_transfer(amount, merchant_address, data):
        assetIssuer = data['asset_issuer']
        assetCode = data['asset_code']
        secret_key = os.getenv("XRP_SEED")
        address = os.getenv("XRP_ADDRESS")
        hash_value = xrp.send_asset(
            address, secret_key, assetCode, amount, merchant_address, assetIssuer)
        return hash_value

    @staticmethod
    def handle_evm_transfer(amount, recipient, currency, data):
        secret_key = os.getenv("pay_account_private_key")
        contract_abi, contract_info = Md().get_contract(currency)
        contract_address = contract_info['contract_address']
        decimals = contract_info['decimals']
        amount_to_send = int(amount) * int(decimals)

        unicorns = web3.eth.contract(
            address=contract_address, abi=contract_abi)

        sender_account = web3.eth.account.privateKeyToAccount(secret_key)
        sender_address = sender_account.address

        tx_hash = connector.make_contract_token_transfer(
            sender_address, recipient, amount, data['gas_price'], data['chain_id'],
            contract_address, contract_abi
        )
        return tx_hash.hex(), contract_address, amount_to_send

    @staticmethod
    def log_transaction(hash_value, service_id, chain, currency, amount_to_send, recipient, data, contract_address):
        sql = {
            "transaction_id": hash_value,
            "service_id": service_id,
            "chain": chain,
            "account_number": data['extra_data']['account_number'],
            "status": "PENDING",
            "currency": currency,
            "amount": amount_to_send,
            "thirdparty_transaction_id": "",
            "source": "sender_address",
            "destination": recipient,
            "request_obj": data
        }
        Db().insert("SentTransaction", **sql)

        message = {
            "txHash": hash_value,
            "currency": os.getenv("coin"),
            "amount": data['amount'],
            "contract_address": contract_address
        }
        return Md.make_response(100, message)


def get_service(service_id, chain):
    url = service_url
    response = requests.request("GET", url)
    data = response.json()
    for x in data:
        if x['service_id'] == service_id and x['chain'] == chain:
            return x
    return []
