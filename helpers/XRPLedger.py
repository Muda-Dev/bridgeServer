from xrpl.wallet import generate_faucet_wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.wallet import Wallet
from helpers.config import rpc_endpoints

xrp_url = rpc_endpoints["XRP"]["url"]

class XRPLedger:
    def __init__(self):
        self.client = JsonRpcClient(xrp_url)  # Define the network client

    def generate_key_pair(self):
        wallet = generate_faucet_wallet(self.client)
        return wallet.classic_address, wallet.seed

    def issue_asset(self, issuer_address, issuer_secret, currency_code, amount, recipient_address):
        payment = Payment(
            account=issuer_address,
            sequence=self.client.get_account_info(issuer_address).result['account_data']['Sequence'],
            fee="10",
            signers=[issuer_address],
            memos=["Asset Issuance"],
            amount=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=issuer_address,
                value=str(amount),
            ),
            destination=recipient_address
        )

        wallet = Wallet(seed=issuer_secret)
        signed_tx = payment.sign(wallet)
        response = self.client.submit(signed_tx)

        return response

    def send_asset(self, sender_address, sender_secret, currency_code, amount, recipient_address, issuer_address):
        payment = Payment(
            account=sender_address,
            sequence=self.client.get_account_info(sender_address).result['account_data']['Sequence'],
            fee="10",
            signers=[sender_address],
            memos=["Asset Transfer"],
            amount=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=issuer_address,
                value=str(amount),
            ),
            destination=recipient_address
        )

        wallet = Wallet(seed=sender_secret)
        signed_tx = payment.sign(wallet)
        response = self.client.submit(signed_tx)

        return response

    def send_xrp(self, sender_address, sender_secret, amount, recipient_address):
        payment = Payment(
            account=sender_address,
            sequence=self.client.get_account_info(sender_address).result['account_data']['Sequence'],
            fee="10",
            signers=[sender_address],
            memos=["XRP Transfer"],
            amount=XRPAmount(
                drops=str(amount),
            ),
            destination=recipient_address
        )

        wallet = Wallet(seed=sender_secret)
        signed_tx = payment.sign(wallet)
        response = self.client.submit(signed_tx)

        return response
