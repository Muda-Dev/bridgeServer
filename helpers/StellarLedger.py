from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset
from stellar_sdk.exceptions import NotFoundError, BadRequestError, Ed25519PublicKeyInvalidError
from stellar_sdk.sep.federation import resolve_stellar_address
import os

class StellarLedger:
    def __init__(self, network="testnet"):
        if network == "public":
            self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
            self.server = Server("https://horizon.stellar.org")
        else:  # Default to testnet
            self.network_passphrase = self.network_passphrase
            self.server = Server("https://horizon.stellar.org")

    def generate_key_pair(self):
        """Generate a Stellar key pair."""
        keypair = Keypair.random()
        return keypair.public_key, keypair.secret

    def get_account_sequence(self, account_id):
        """Retrieve the current sequence number for an account."""
        account = self.server.load_account(account_id)
        return account.sequence

    def create_account(self, funder_secret, new_account_public_key, starting_balance="10"):
        """Create and fund a new Stellar account."""
        funder_keypair = Keypair.from_secret(funder_secret)
        funder_account = self.server.load_account(account_id=funder_keypair.public_key)
        transaction = (
            TransactionBuilder(
                source_account=funder_account,
                network_passphrase=self.network_passphrase,  # Switch as necessary
                base_fee=None  # Let SDK compute this automatically
            )
            .append_create_account_op(
                destination=new_account_public_key,
                starting_balance=starting_balance  # Minimum is 1 XLM on public network
            )
            .build()
        )
        transaction.sign(funder_keypair)
        try:
            response = self.server.submit_transaction(transaction)
            return response
        except Exception as e:
            return str(e)

    def check_balance(self, account_id):
        """Check balance for a Stellar account."""
        account = self.server.accounts().account_id(account_id).call()
        balances = account['balances']
        return balances

    def send_asset(self, sender_secret, recipient_address, asset_code, amount, issuer=None):
        """Send an asset (including native XLM) to a specified account."""
        sender_keypair = Keypair.from_secret(sender_secret)
        sender_account = self.server.load_account(account_id=sender_keypair.public_key)
        asset = Asset(asset_code, issuer) if asset_code != "XLM" else Asset.native()

        transaction = (
            TransactionBuilder(
                source_account=sender_account,
                network_passphrase=self.network_passphrase,  # Switch as necessary
                base_fee=None  # Let SDK compute this automatically
            )
            .append_payment_op(
                destination=recipient_address,
                amount=amount,
                asset_code=asset.code,
                asset_issuer=asset.issuer
            )
            .build()
        )
        transaction.sign(sender_keypair)
        try:
            response = self.server.submit_transaction(transaction)
            return response
        except Exception as e:
            return str(e)

    def change_trust(self, account_secret, asset_code, issuer, limit="1000000000"):
        """Create or update a trustline."""
        account_keypair = Keypair.from_secret(account_secret)
        account = self.server.load_account(account_id=account_keypair.public_key)
        asset = Asset(asset_code, issuer)

        transaction = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=self.network_passphrase,  # Switch as necessary
                base_fee=None  # Let SDK compute this automatically
            )
            .append_change_trust_op(asset_code=asset.code, asset_issuer=asset.issuer, limit=limit)
            .build()
        )
        transaction.sign(account_keypair)
        try:
            response = self.server.submit_transaction(transaction)
            return response
        except Exception as e:
            return str(e)
