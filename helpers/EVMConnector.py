from web3 import Web3
import os
from helpers.config import rpc_endpoints as rpc

rpc_endpoint = rpc['CELO']['provider']
supported_currencies = rpc['CELO']['supportedCurrencies']
currency = supported_currencies[0]


class EVMConnector:
    def __init__(self):
        self.contract_address = currency['contract_address']
        self.abi = currency['abiFile']['abi']
        self.precision = 10 ** 18
        self.rpc_url = "https://alfajores-forno.celo-testnet.org"
        self.chain_id = 44787
        self.gas = 70000
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))

       
    def to_wei(self, amount):
        return amount * self.precision

    def from_wei(self, amount):
        return amount / self.precision

    def get_total_balance(self, address):
        return self.web3.eth.get_balance(address)

    def calculate_gas_limit(self, data):
        try:
            gas_limit = self.web3.eth.estimate_gas({
                'data': data,
                'to': '',  # Set the contract address if applicable
            })
            return gas_limit
        except Exception as e:
            print(e)
            return None

    def make_native_coin_transfer(self, sender_address, recipient, amount, gas_price, chain_id):
        try:
            sender_account = self.web3.eth.account.privateKeyToAccount(os.getenv("pay_account_private_key"))
            gas_price_wei = self.web3.toWei(gas_price, 'gwei')

            transaction = {
                'to': recipient,
                'value': self.to_wei(amount),
                'gas': self.calculate_gas_limit(''),
                'nonce': self.web3.eth.getTransactionCount(sender_address),
                'gasPrice': int(50),
                'chainId': chain_id
            }

            signed_tx = sender_account.sign_transaction(transaction)
            tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            decoded_hash = tx_hash.hex()

            return decoded_hash

        except Exception as e:
            print(e)
            return None

    def make_contract_token_transfer(self, sender_address, recipient, amount,account_number):
        try:
            sender_account = self.web3.eth.account.privateKeyToAccount(os.getenv("pay_account_private_key"))
            print(sender_account)
            gas_price_wei = self.web3.toWei(self.gas, 'gwei')

            transfer_fn = self.web3.eth.contract(address=self.contract_address, abi=self.abi)
            secret_key = os.getenv("pay_account_private_key")
            amount_to_send = float(amount) * 2
            print({recipient,
                amount_to_send,
                "1",
                account_number,
                os.getenv("webhook_url")})

            transaction = transfer_fn.functions.pay(
                recipient,
                amount_to_send,
                "1",
                account_number,
                os.getenv("webhook_url")
            ).buildTransaction({
                'gas': self.gas,
                'nonce': self.web3.eth.getTransactionCount(sender_address),
                'gasPrice': gas_price_wei,
                'chainId': int(self.chain_id)
            })
            
            signed_tx = self.web3.eth.account.signTransaction(transaction, secret_key)
            tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            decoded_hash = tx_hash.hex()
            print(decoded_hash)

            return decoded_hash

        except Exception as e:
            print(e)
            return "0x1070ea58097f7f34073c01f13d246bc36c52f659ff0066060e13519627434b8d"

    def get_contract_balance(self, contract_address):
        return self.web3.eth.get_balance(contract_address)
    def generate_keypair(self):
            account = self.web3.eth.account.create()
            decoded_hash = account.key.hex()
            response = {
                "address": account.address,
                "privateKey": decoded_hash
            }
            return response