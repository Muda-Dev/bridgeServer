from flask import jsonify
from celo_sdk.kit import Kit
from celo_sdk.wallet import Wallet
from libs.database import Database as Db
from libs.modal import Modal as Md
from web3 import Web3
import requests
import json
from config import muda_endpoint as muda


class Account:
    def __init__(self):
        self.kit = Kit('https://alfajores-forno.celo-testnet.org')
        self.wallet = Wallet
        self.precision = 1000000000000000000
        self.abi = Md().get_abi()
        self.contract_address = "0xF17DB59dA5ddc58E08de2AD83478391Ab9797d50"
        self.token_code = "UGXT"

    def to_wei(self, amount):
        return amount * self.precision

    def from_wei(self, amount):
        return amount / self.precision

    def generate_keypair(self):
        account = self.kit.w3.eth.account.create()
        print(account)
        return account

    def make_transfer(self, rq):
        try:
            data = rq.json
            print("transaction request received")
            amount = data['amount']
            recipient = data['recipient']
            secret_key = data['sending_secret_key']
            extra_data = data['extra_data']
            sending_token = data['sending_token']
            service_id = extra_data['service_id']
            account_number = extra_data['account_number']
            service_info = get_service(service_id)

            if amount <= 0:
                return Md.make_response(404, "invalid amount")

            if len(service_info) == 0:
                return Md.make_response(404, "service not found")

            merchant_celo_address = service_info['merchant_celo_address']
            if recipient != merchant_celo_address:
                return Md.make_response(404, "sent recipient address does not match receiver address")

            amount_to_send = amount * 100

            unicorns = self.kit.w3.eth.contract(address=self.contract_address, abi=self.abi)
            print(unicorns.address)

            sending_contract_token = self.kit.base_wrapper.create_and_get_contract_by_name('GoldToken')
            gas_price_contract = self.kit.base_wrapper.create_and_get_contract_by_name('GasPriceMinimum')
            gas_price_minimum = gas_price_contract.get_gas_price_minimum(sending_contract_token.address)
            gas_price = int(gas_price_minimum * 3)
            FROM_ADDR = "0xF968575Dc8872D3957E3b91BFAE0d92D4c9c1Dd5"

            transaction = unicorns.functions.transfer(
                recipient,
                amount_to_send
            ).buildTransaction({
                'gas': 70000,
                'nonce': self.kit.w3.eth.getTransactionCount(FROM_ADDR),
                'gasPrice': gas_price,
                'chainId': 44787
            })
            signed_tx = self.kit.w3.eth.account.signTransaction(transaction, secret_key)
            print(signed_tx)
            tx_hash = self.kit.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            decoded_hash = tx_hash.hex()

            send_data = {
                "account_id": FROM_ADDR,
                "amount": amount,
                "currency": "UGX",
                "sent_from": FROM_ADDR,
                "sent_to": recipient,
                "service_id": service_id,
                "recipient_account_number": account_number,
                "txn_hash": decoded_hash
            }
            muda_response = send_transaction(send_data)
            print(muda_response)
            return Md.make_response(100, decoded_hash)

        except Exception as e:
            return Md.make_response(203, "transaction failed " + str(e))

    def get_account_balance(self, address):
        try:
            unicorns = self.kit.w3.eth.contract(address=self.contract_address, abi=self.abi)
            balance = unicorns.functions.balanceOf(address).call()

            account = self.kit.get_total_balance(address)
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
            contract_info = self.kit.w3.eth.contract(ugx_contract)
            function = contract_info.functions.name().call()
            print(function)

        except Exception as e:
            print(e)

    def celo_contract_transfer(self, rq):
        try:
            data = rq.json
            print("transaction request received")
            recipient = data['recipient']
            amount = data['amount']
            secret_key = data['sending_secret_key']
            extra_data = data['extra_data']
            sending_token = data['sending_token']
            # Log request transaction
            print("amount", str(amount) + " " + sending_token)
            print("recipient", recipient)
            print("extra_data", extra_data)
            log_transaction(0, recipient, amount, sending_token, extra_data)

            self.kit.wallet_add_new_key = secret_key
            # accounts = self.kit.wallet.accounts
            amount_to_wei = self.kit.w3.toWei(amount, 'ether')

            if sending_token == "cUSD":
                sending_contract_token = self.kit.base_wrapper.create_and_get_contract_by_name('StableToken')
                gas_price_contract = self.kit.base_wrapper.create_and_get_contract_by_name('GasPriceMinimum')
                gas_price_minimum = gas_price_contract.get_gas_price_minimum(sending_contract_token.address)
                gas_price = int(gas_price_minimum * 1.3)
                self.kit.wallet_fee_currency = sending_contract_token.address  # Default to paying fees in cUSD
                self.kit.wallet_gas_price = gas_price
            elif sending_token == "CELO":
                sending_contract_token = self.kit.base_wrapper.create_and_get_contract_by_name('GoldToken')
                gas_price_contract = self.kit.base_wrapper.create_and_get_contract_by_name('GasPriceMinimum')
                gas_price_minimum = gas_price_contract.get_gas_price_minimum(sending_contract_token.address)
                print("gas_price_minimum", gas_price_minimum)
                gas_price = int(gas_price_minimum * 3)
                self.kit.wallet_gas_price = gas_price

            else:
                return Md.make_response(203, "currency not supported")
            print("gas_price", gas_price)

            tx = sending_contract_token.transfer(recipient, amount_to_wei)
            decoded_hash = tx.hex()
            log_transaction(decoded_hash, recipient, amount, sending_token, extra_data)

            return Md.make_response(100, "transaction request sent", decoded_hash)
        except Exception as e:
            return Md.make_response(203, "transaction failed " + str(e))


def get_service(service_id):
    url = muda + "service/" + service_id
    response = requests.request("GET", url)
    return response.json()


def send_transaction(data):
    url = muda + "account/make_payment"

    payload = json.dumps(data)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def log_transaction(decoded_hash, recipient, amount, sending_token, extra_data):
    # save txn to local db
    return True


def auth_user(username, password):
    values = {"username": username, "password": password}
    data = Db.select("sia_user", "*", **values)
    return data
