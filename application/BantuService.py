import time
from stellar_sdk.server import Server
from stellar_sdk.exceptions import NotFoundError, BadRequestError
import os
from dotenv import load_dotenv
import threading
from helpers.dbhelper import Database as Db
from helpers.modal import Modal as md
import logging


load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
stellar_logger = logging.getLogger(__name__)

# Initialize the server
server = Server("https://expansion.bantu.network")


def save_cursor(cursor, chain="bantu"):
    Db().Update(
        "ChainBlock", "chain='bantu'", **{"chain": chain, "last_seen_block": cursor}
    )
    return True


def get_last_cursor(chain="bantu"):
    result = Db().select(
        "SELECT last_seen_block FROM ChainBlock WHERE chain = %s", (chain,)
    )
    if result:
        return result[0]["last_seen_block"]
    return "now"  # Default to "now" if no cursor is stored


def listen_for_transactions(account_id):
    last_cursor = get_last_cursor()
    save_cursor(last_cursor)
    while True:
        try:
            print("Starting transaction stream...")
            transaction_stream = (
                server.transactions()
                .for_account(account_id)
                .cursor(last_cursor)
                .stream()
            )
            for transaction in transaction_stream:
                on_transaction_received(transaction)
                last_cursor = transaction["paging_token"]
                save_cursor(last_cursor)
        except Exception as e:
            print(
                f"An error occurred during streaming: {e}. Attempting to restart stream..."
            )
            time.sleep(5)


def process_operations(transaction):
    # print("Transaction Information==>",transaction )
    operations = server.operations().for_transaction(transaction["id"]).call()
    for op in operations["_embedded"]["records"]:
        if op["type"] == "payment":
            # Check the asset type
            asset_type = op.get("asset_type")
            if asset_type in ("credit_alphanum4", "credit_alphanum12"):
                asset_code = op.get("asset_code")
                asset_issuer = op.get("asset_issuer")
                # Check for specified assets by code and issuer
                print("received asset operation ==>", op)
                if (
                    asset_code == "USDC"
                    and asset_issuer == os.getenv("USDC_ISSUER")
                    or asset_code == "cUGX"
                    and asset_issuer == os.getenv("CUGX_ISSUER")
                ):
                    return {
                        "asset": asset_code,
                        "from":op.get("from"),
                        "to":op.get("to"),
                        "issuer": asset_issuer,
                        "amount": op.get("amount"),
                    }
    return False


def on_transaction_received(transaction):
    print("new transaction received")
    single_op =  process_operations(transaction)
    if single_op !=False:
        print(f"Transaction {transaction['id']} involves XLM, USDC, or cUGX.")
        id = transaction["id"]
        asset_amount = single_op['amount']
        asset_issuer = single_op['issuer']
        from_account = single_op['from']
        to_account = single_op['to']
        asset_code = single_op['asset']
        memo = transaction['memo']
        
        md.payout_callback(id, to_account, from_account, asset_amount, asset_code, asset_issuer, "BANTU",memo
        )
        # Additional processing can be added here


async def main():
    account_id = os.getenv("STELLAR_ACCOUNT_ID")
    if not account_id:
        stellar_logger.error("Please set the 'STELLAR_ACCOUNT_ID' environment variable.")
        return

    stellar_logger.info("Starting Stellar transaction listener asynchronously")
    
    # Ensure listen_for_transactions is async, otherwise run in a separate thread
    await asyncio.to_thread(listen_for_transactions, account_id)