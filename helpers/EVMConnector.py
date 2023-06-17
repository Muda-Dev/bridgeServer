from web3 import Web3
from config import config as cfg
import os


class EVMConnector:
    def __init__(self, contract_address, abi, rpc_url, chain_id):
        self.contract_address = contract_address
        self.abi = abi
        self.precision = 10 ** 18

        self.rpc_url = rpc_url
        self.chain_id = chain_id
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
                'gasPrice': gas_price_wei,
                'chainId': chain_id
            }

            signed_tx = sender_account.sign_transaction(transaction)
            tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            decoded_hash = tx_hash.hex()

            return decoded_hash

        except Exception as e:
            print(e)
            return None

    def make_contract_token_transfer(self, sender_address, recipient, amount, gas_price, chain_id, contract_address, abi):
        try:
            sender_account = self.web3.eth.account.privateKeyToAccount(os.getenv("pay_account_private_key"))
            gas_price_wei = self.web3.toWei(gas_price, 'gwei')

            contract = self.web3.eth.contract(address=contract_address, abi=abi)
            transfer_fn = contract.functions.transfer(recipient, amount)
            transaction = transfer_fn.buildTransaction({
                'gas': self.calculate_gas_limit(transfer_fn.encodeABI()),
                'nonce': self.web3.eth.getTransactionCount(sender_address),
                'gasPrice': gas_price_wei,
                'chainId': chain_id
            })

            signed_tx = sender_account.sign_transaction(transaction)
            tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            decoded_hash = tx_hash.hex()

            return decoded_hash

        except Exception as e:
            print(e)
            return None

    def get_contract_balance(self, contract_address):
        return self.web3.eth.get_balance(contract_address)
