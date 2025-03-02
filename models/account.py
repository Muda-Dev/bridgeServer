from abc import ABC, abstractmethod
import traceback
from flask import jsonify
import requests
import os
from helpers.EVMConnector import EVMConnector
from helpers.StellarLedger import StellarLedger
from helpers.dbhelper import Database as Db
from helpers.modal import Modal as Md
from helpers.config import service_url
from tronpy.keys import PrivateKey
from tronpy import Tron
from tronpy.providers import HTTPProvider


class BlockchainInterface(ABC):
    @abstractmethod
    def generate_keypair(self):
        pass

    @abstractmethod
    def get_balance(self, address):
        pass

    @abstractmethod
    def get_transaction(self, hash):
        pass

class TRONBlockchain(BlockchainInterface):
    def __init__(self):
        self.tron = Tron(HTTPProvider(api_key=os.getenv("c7ecb219-8949-447f-816a-d28aa562e303")))

    def generate_keypair(self):
        private_key = PrivateKey.random()
        public_address = private_key.public_key.to_base58check_address()
        print(f"Private Key: {private_key.hex()}")
        print(f"Public Address: {public_address}")
        return {"address": public_address, "privateKey": private_key.hex()}

 
    def get_balance(self, address):
        return self.tron.get_account_balance(address)

    def get_transaction(self, hash):
        return self.tron.get_transaction(hash)

class StellarBlockchain(BlockchainInterface):
    def __init__(self):
        self.stellar = (
            StellarLedger()
        )  # Assuming StellarLedger is imported and available

    def generate_keypair(self):
        public_key, secret = self.stellar.generate_key_pair()
        return {"public_key": public_key, "secret": secret}

    def get_balance(self, address):
        balances = self.stellar.check_balance(address)
        # Process balances to fit your return format if necessary
        return balances

    def get_transaction(self, hash):
        transaction = self.stellar.get_single_transaction(hash)
        # Process transaction to fit your return format if necessary
        return transaction


class EVMBlockchain(BlockchainInterface):
    def __init__(self):
        self.evm = EVMConnector()

    def generate_keypair(self):
        return self.evm.generate_keypair()

    def get_balance(self, address):
        return self.evm.get_total_balance(address)

    def get_transaction(self, hash):
        return self.evm.get_transaction_by_hash(hash)


class XRPBlockchain(BlockchainInterface):
    def __init__(self):
        self.xrp = None  # XRPLedger()

    def generate_keypair(self):
        classic_address, seed = self.xrp.generate_key_pair()
        return {"classic_address": classic_address, "seed": seed}

    def get_balance(self, address):
        return self.xrp.check_balance(address)

    def get_transaction(self, hash):
        return self.xrp.get_single_transaction(hash)


class BlockchainFactory:
    def get_blockchain(self, blockchain_name):
        blockchains = {
            "ETH": EVMBlockchain,
            "CELO": EVMBlockchain,
            "BSC": EVMBlockchain,
            "XRP": XRPBlockchain,
            "XLM": StellarBlockchain,
            "TRX": TRONBlockchain,
        }

        blockchain = blockchains.get(blockchain_name.upper())
        if not blockchain:
            raise ValueError("Invalid blockchain name")
        return blockchain()


class Account:
    def __init__(self):
        self.blockchain_factory = BlockchainFactory()

    def generate_keypair(self, request):
        try:
            data = request.json
            print("here",data)
            blockchain_name = data["chain"]
            chain_info = self.get_provider_addresses(blockchain_name)
            print("Chain Info:", chain_info)
            if chain_info:
                return {"address": chain_info[0]['address'], "seed": chain_info[0]['private_key'], "chain": blockchain_name,"memo": chain_info[0]['memo']}
            blockchain_instance = self.blockchain_factory.get_blockchain(
                blockchain_name
            )
            keypair = blockchain_instance.generate_keypair()
            if blockchain_name in ["ETH","CELO", "TRX","BSC"]:
                address = keypair['address']
                privateKey = keypair['privateKey']
                obj = {"address": address,"seed": privateKey,"chain":blockchain_name}
                Db().insert("addresses", **obj)
            return keypair
        except Exception as e:
            print("An error occurred:", e)
            traceback.print_exc()
            return {}
            
            
    def get_balance(self, request):
        data = request.json
        address = data["address"]
        blockchain_name = data["chain"]
        blockchain_instance = self.blockchain_factory.get_blockchain(blockchain_name)
        return blockchain_instance.get_balance(address)

    def get_transaction(self, request):
        data = request.json
        tx_hash = data["hash"]
        blockchain_name = data["chain"]
        blockchain_instance = self.blockchain_factory.get_blockchain(blockchain_name)
        return blockchain_instance.get_transaction(tx_hash)

    def make_transfer(self, request):
        try:
            data = request.json
            amount = float(data["amount"])
            recipient = str(data["recipient"])
            extra_data = data.get("extra_data", {})
            service_id = extra_data.get("service_id", "")
            chain = extra_data.get("chain", "")
            currency = str(data["currency"])
            account_number = extra_data["account_number"]

            if not amount or amount <= 0:
                return Md.make_response(404, "invalid amount")

            service_info = self.get_service(service_id, chain)
            merchant_address = service_info.get("evm_Address", "")

            if not service_info:
                return Md.make_response(404, "service not found")

            if recipient != merchant_address:
                return Md.make_response(
                    404, "sent recipient address does not match receiver address"
                )

            if chain == "XRP":
                hash_value = Account.handle_xrp_transfer(amount, merchant_address, data)

            else:
                # Assuming this means EVM
                sending_amount = str(amount)
                hash_value = evc.make_contract_token_transfer(
                    os.getenv("address"),
                    merchant_address,
                    sending_amount,
                    account_number,
                )

            return Account.log_transaction(
                hash_value, service_id, chain, currency, amount, recipient, data
            )

        except Exception as e:
            return Md.make_response(203, "transaction failed " + str(e))

    @staticmethod
    def handle_evm_transfer(self, amount, merchant_address, data):
        gas_price = data.get("gas_price", 0)
        chain_id = data.get("chain_id", 0)

        # assuming amount is in ETH for native coin transfer
        hash_value = self.evm.make_native_coin_transfer(
            Account.SECRET_KEY, merchant_address, amount, gas_price, chain_id
        )

        return hash_value

    @staticmethod
    def create_account(request):
        data = request.json
        sender_address = data["sender_address"]
        sender_secret = data["sender_secret"]
        new_account_address = data["new_account_address"]
        amount = data["amount"]  # Should be at least 20 XRP (20000000 drops)
        response = xrp.create_account(
            sender_address, sender_secret, new_account_address, amount
        )
        return response

    @staticmethod
    def check_balance(request):
        data = request.json
        address = data["address"]
        balance = xrp.check_balance(address)
        return balance

    @staticmethod
    def get_transaction(request):
        data = request.json
        hash = data["hash"]
        transaction = xrp.get_single_transaction(hash)
        return transaction

    @staticmethod
    def fund_account(request):
        data = request.json
        sender_address = data["sender_address"]
        sender_secret = data["sender_secret"]
        recipient_address = data["recipient_address"]
        amount = data["amount"]
        response = xrp.fund_account(
            sender_address, sender_secret, recipient_address, amount
        )
        return response

    @staticmethod
    def make_path_payment(request):
        data = request.json
        sender_address = data["sender_address"]
        sender_secret = data["sender_secret"]
        recipient_address = data["recipient_address"]
        source_currency = data["source_currency"]
        source_issuer = data["source_issuer"]
        source_amount = data["source_amount"]
        destination_currency = data["destination_currency"]
        destination_issuer = data["destination_issuer"]
        destination_amount = data["destination_amount"]
        response = xrp.make_path_payment(
            sender_address,
            sender_secret,
            recipient_address,
            source_currency,
            source_issuer,
            source_amount,
            destination_currency,
            destination_issuer,
            destination_amount,
        )
        return response

    @staticmethod
    def log_transaction(
        hash_value, service_id, chain, currency, amount, recipient, data
    ):
        sql = {
            "transaction_id": hash_value,
            "service_id": service_id,
            # "chain": chain,
            "account_number": data["extra_data"]["account_number"],
            "status": "PENDING",
            "currency": currency,
            "amount": amount,
            "thirdparty_transaction_id": "",
            "source": "sender_address",
            "destination": recipient,
            "request_obj": data,
        }
        Db().insert("SentTransaction", **sql)

        message = {
            "txHash": hash_value,
            "currency": os.getenv("coin"),
            "amount": data["amount"],
        }
        return Md.make_response(100, message)

    def get_provider_addresses(self, chain):
        query = "SELECT * FROM provider_addresses WHERE chain = %s"
        result = Db().select(query, (chain))
        if result:
            return result
        return {}

    def get_service(service_id, chain):
        url = service_url
        response = requests.get(url)
        data = response.json()
        for entry in data:
            if entry.get("service_id") == service_id:
                return entry
        return {}
