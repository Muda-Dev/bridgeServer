from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset
from stellar_sdk.exceptions import NotFoundError, BadRequestError, Ed25519PublicKeyInvalidError
from stellar_sdk.sep.federation import resolve_stellar_address
import os
import logging

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class StellarLedger:
    def __init__(self, network="testnet"):
        if network == "public":
            self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
            self.server = Server("https://horizon.stellar.org")
        else:  # Default to testnet
            self.network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
            self.server = Server("https://horizon-testnet.stellar.org")
        logger.info("Initialized StellarLedger with network: %s", network)

    def generate_key_pair(self):
        """Generate a Stellar key pair."""
        keypair = Keypair.random()
        logger.info("Generated key pair with public key: %s", keypair.public_key)
        return keypair.public_key, keypair.secret

    def get_account_sequence(self, account_id):
        """Retrieve the current sequence number for an account."""
        try:
            account = self.server.load_account(account_id)
            logger.info("Retrieved sequence number for account %s: %s", account_id, account.sequence)
            return account.sequence
        except Exception as e:
            logger.error("Failed to retrieve sequence for account %s: %s", account_id, e)
            raise

    def create_account(self, funder_secret, new_account_public_key, starting_balance="10"):
        """Create and fund a new Stellar account."""
        funder_keypair = Keypair.from_secret(funder_secret)
        logger.info("Loaded funder account: %s", funder_keypair.public_key)
        try:
            funder_account = self.server.load_account(account_id=funder_keypair.public_key)
            transaction = (
                TransactionBuilder(
                    source_account=funder_account,
                    network_passphrase=self.network_passphrase,
                    base_fee=None
                )
                .append_create_account_op(
                    destination=new_account_public_key,
                    starting_balance=starting_balance
                )
                .build()
            )
            transaction.sign(funder_keypair)
            response = self.server.submit_transaction(transaction)
            logger.info("Successfully created account %s with starting balance: %s", new_account_public_key, starting_balance)
            return response
        except Exception as e:
            logger.error("Failed to create account %s: %s", new_account_public_key, e)
            return str(e)

    def check_balance(self, account_id):
        """Check balance for a Stellar account."""
        try:
            account = self.server.accounts().account_id(account_id).call()
            balances = account['balances']
            logger.info("Retrieved balances for account %s: %s", account_id, balances)
            return balances
        except Exception as e:
            logger.error("Failed to retrieve balance for account %s: %s", account_id, e)
            return []

    def send_asset(self, sender_secret, recipient_address, asset_code, amount, issuer=None):
        """Send an asset (including native XLM) to a specified account."""
        sender_keypair = Keypair.from_secret(sender_secret)
        logger.info("Loaded sender account: %s", sender_keypair.public_key)
        try:
            sender_account = self.server.load_account(account_id=sender_keypair.public_key)
            asset = Asset(asset_code, issuer) if asset_code != "XLM" else Asset.native()

            transaction = (
                TransactionBuilder(
                    source_account=sender_account,
                    network_passphrase=self.network_passphrase,
                    base_fee=None
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
            response = self.server.submit_transaction(transaction)
            logger.info("Successfully sent %s %s to %s", amount, asset_code, recipient_address)
            return response
        except Exception as e:
            logger.error("Failed to send asset %s to %s: %s", asset_code, recipient_address, e)
            return str(e)

    def change_trust(self, account_secret, asset_code, issuer, limit="1000000000"):
        """Create or update a trustline."""
        account_keypair = Keypair.from_secret(account_secret)
        logger.info("Loaded account for trustline update: %s", account_keypair.public_key)
        try:
            account = self.server.load_account(account_id=account_keypair.public_key)
            asset = Asset(asset_code, issuer)

            transaction = (
                TransactionBuilder(
                    source_account=account,
                    network_passphrase=self.network_passphrase,
                    base_fee=None
                )
                .append_change_trust_op(asset_code=asset.code, asset_issuer=asset.issuer, limit=limit)
                .build()
            )
            transaction.sign(account_keypair)
            response = self.server.submit_transaction(transaction)
            logger.info("Successfully changed trustline for asset %s issued by %s with limit %s", asset_code, issuer, limit)
            return response
        except Exception as e:
            logger.error("Failed to change trustline for asset %s: %s", asset_code, e)
            return str(e)
