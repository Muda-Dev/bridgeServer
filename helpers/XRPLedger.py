from xrpl.wallet import generate_faucet_wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment, TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.wallet import Wallet
from helpers.config import rpc_endpoints
from xrpl.models.transactions.transaction import Signer

xrp_url = rpc_endpoints["XRP"]["url"]

class XRPLedger:
    def __init__(self):
        self.client = JsonRpcClient(xrp_url)  # Define the network client

    def generate_key_pair(self):
        wallet = generate_faucet_wallet(self.client)
        return wallet.classic_address, wallet.seed

    def create_account(self, sender_address, sender_secret, new_account_address):
        # operation to fund a new account, we have set 20XRP has the minimum amount to create this account
        amount = "20"
        return self.send_xrp(sender_address, sender_secret, amount, new_account_address)

    def check_balance(self, address):
        response = self.client.get_account_info(address)
        return response.result['account_data']['Balance']

    def get_single_transaction(self, hash):
        response = self.client.get_transaction(hash)
        return response

    def has_trustline(self, address, asset_issuer, asset_code):
        trustlines = self.client.get_account_lines(address).result['lines']
        for trustline in trustlines:
            if trustline['account'] == asset_issuer and trustline['currency'] == asset_code:
                return True
        return False

    def path_payment(self, sender_address, sender_secret, paths, send_currency, send_max, dest_address, dest_currency, dest_amount):
        payment = Payment(
            account=sender_address,
            sequence=self.client.get_account_info(sender_address).result['account_data']['Sequence'],
            fee="10",
            signers=[Signer(account=sender_address, tx_signing_key=sender_secret)],
            paths=paths,
            send_currency=send_currency,
            send_max=send_max,
            destination=dest_address,
            dest_currency=dest_currency,
            dest_amount=dest_amount
        )

        wallet = Wallet(seed=sender_secret)
        signed_tx = payment.sign(wallet)
        response = self.client.submit(signed_tx)

        return response

    def set_multisignature(self, address, secret, signer_entries):
        signer_list_set = SignerListSet(
            account=address,
            sequence=self.client.get_account_info(address).result['account_data']['Sequence'],
            fee="10",
            signer_entries=[SignerEntry(
                account=signer['account'], weight=signer['weight']) for signer in signer_entries],
            signer_quorum=sum(signer['weight'] for signer in signer_entries)
        )

        wallet = Wallet(seed=secret)
        signed_tx = signer_list_set.sign(wallet)
        response = self.client.submit(signed_tx)

        return response

    def issue_asset(self, issuer_address, issuer_secret, currency_code, amount, recipient_address):
        payment = Payment(
            account=issuer_address,
            sequence=self.client.get_account_info(issuer_address).result['account_data']['Sequence'],
            fee="10",
            signers=[Signer(account=issuer_address, tx_signing_key=issuer_secret)],
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
            signers=[Signer(account=sender_address, tx_signing_key=sender_secret)],
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
            signers=[Signer(account=sender_address, tx_signing_key=sender_secret)],
            memos=["XRP Transfer"],
            amount=IssuedCurrencyAmount(currency="XRP", issuer="", value=str(amount)),
            destination=recipient_address
        )

        wallet = Wallet(seed=sender_secret)
        signed_tx = payment.sign(wallet)
        response = self.client.submit(signed_tx)

        return response

    def change_trust(self, account_address, account_secret, currency_code, issuer_address, limit):
        trustset = TrustSet(
            account=account_address,
            sequence=self.client.get_account_info(account_address).result['account_data']['Sequence'],
            fee="10",
            limit_amount=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=issuer_address,
                value=str(limit),
            ),
        )

        wallet = Wallet(seed=account_secret)
        signed_tx = trustset.sign(wallet)
        response = self.client.submit(signed_tx)

        return response
