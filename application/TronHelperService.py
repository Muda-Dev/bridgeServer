import os
import sys
import asyncio
import logging
import traceback
from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.exceptions import BlockNotFound
from tronpy.keys import to_base58check_address, to_hex_address
from helpers.modal import Modal as md
from helpers.dbhelper import Database as Db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
tron_logger = logging.getLogger(__name__)

# Configuration from environment variables
ENVIRONMENT = os.getenv("ENV", "stage")
API_KEYS = os.getenv("TRON_API_KEYS", "").split(",")
usdt_contract_address = os.getenv("CONTRACT")

current_key_index = 0

def get_next_api_key():
    global current_key_index
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return key

def get_tron_client():
    env = os.getenv("ENV", "stage")  # Use "mainnet" as default
    if env.lower() == "stage":
        return Tron(HTTPProvider(endpoint_uri="https://api.nileex.io"))
    else:
        return Tron(HTTPProvider(api_key=get_next_api_key()))


tron = get_tron_client()

# Database functions
def save_last_seen_block_number(block_number):
    print("Saved block", block_number)
    Db().Update("ChainBlock", "chain='tron'", **{"last_seen_block": block_number})
    return True

def load_last_seen_block_number():
    db = Db()
    result = db.select(
        "SELECT last_seen_block FROM ChainBlock WHERE chain = %s", ("tron",)
    )
    if result:
        last_seen = int(result[0]["last_seen_block"])
        if last_seen == 0:
            tron_logger.info("Last seen block is 0. Starting from the current block.")
            return tron.get_latest_block_number()
        else:
            return last_seen
    else:
        # Get the current block number if no block is stored
        tron_logger.info("No saved block found. Starting from the current block.")
        return tron.get_latest_block_number()


def get_payment_addresses():
    db = Db()
    result = db.select("SELECT address FROM addresses WHERE chain='TRX' and status='active'")
    return [row["address"] for row in result]

# Event processing
def handle_event(transaction, currency):
    tron_logger.info("Step 1: Received a new event: %s", transaction)

    try:
        tron_logger.info("Step 2: Extracting transaction hash.")
        transaction_hash = transaction['txID']
        
        tron_logger.info("Step 3: Extracting raw data from the transaction.")
        raw_data = transaction['raw_data']['contract'][0]['parameter']['value']

        tron_logger.info("Step 4: Decoding owner and contract addresses.")
        owner_address = to_base58check_address(raw_data.get("owner_address"))
        contract_address = to_base58check_address(raw_data.get("contract_address"))

        tron_logger.info("Step 5: Extracting and decoding the 'data' field.")
        data = raw_data.get("data")

        # Extract recipient address from 'data'
        recipient_hex = "0x" + data[8:72].lstrip("0")  # Remove leading zeroes
        if len(recipient_hex) < 42:  # Check if the hex address is valid
            tron_logger.error("Step 5 Error: Invalid recipient address: %s", recipient_hex)
            return False
        recipient_address = to_base58check_address(recipient_hex)

        # Extract amount from 'data'
        amount_hex = data[72:]
        tron_logger.info("Step 6: Extracting amount from data.")
        try:
            amount = int(amount_hex, 16)  # Convert hex to decimal
        except ValueError as ve:
            tron_logger.error("Error converting amount from hex: %s", ve)
            return False

        # Convert the raw amount to human-readable format
        asset_amount = amount / (10 ** currency["decimals"])
        tron_logger.info(
            f"Step 7: Decoded details - From {owner_address}, To {recipient_address}, "
            f"Raw Amount {amount}, Human-Readable Amount {asset_amount}"
        )

        tron_logger.info("Step 8: Verifying the contract address matches the monitored contract.")
        if contract_address != currency['contract_address']:
            tron_logger.info("Ignoring transaction for unrelated contract: %s", contract_address)
            return False

        tron_logger.info("Step 9: Fetching payment addresses from the database.")
        payment_addresses = get_payment_addresses()

        tron_logger.info("Step 10: Checking if recipient address is in monitored addresses.")
        if recipient_address in payment_addresses:
            # Pass only parsed data to process_received_data
            process_received_data(
                transaction_hash=transaction_hash,
                from_address=owner_address,
                to_address=recipient_address,
                asset_amount=asset_amount,  # Use the human-readable amount here
                currency=currency,
            )
        else:
            tron_logger.info("Recipient address not in monitored addresses: %s", recipient_address)
        return True
    except Exception as e:
        tron_logger.error("Failed to process event: %s", e)
        traceback.print_exc()
        return False


def process_received_data(transaction_hash, from_address, to_address, asset_amount, currency):
    try:
        tron_logger.info("Processing transaction: %s", transaction_hash)

        # Log the requested variables
        tron_logger.info("Transaction details:")
        tron_logger.info("Transaction Hash: %s", transaction_hash)
        tron_logger.info("From Address: %s", from_address)
        tron_logger.info("To Address: %s", to_address)
        tron_logger.info("Asset Amount: %.6f", asset_amount)
        tron_logger.info("Currency Code: %s", currency["code"])
        tron_logger.info("Contract Address: %s", currency["contract_address"])
        tron_logger.info("Network: tron")

        # Execute the callback
        md.payout_callback(
            transaction_hash,
            from_address,
            to_address,
            asset_amount,
            currency["code"],
            currency["contract_address"],
            "tron",
        )

        return True

    except Exception as e:
        tron_logger.error("Error while processing transaction: %s", e)
        traceback.print_exc()
        return False

# Main event loop
async def log_loop(poll_interval, currency):
    last_seen_block = load_last_seen_block_number()
    tron_logger.info("Last checked block: %s", last_seen_block)

    while True:
        try:
            current_block_number = tron.get_latest_block_number()
            tron_logger.info("Current block number: %s", current_block_number)

            for block_number in range(last_seen_block + 1, current_block_number + 1):
                try:
                    tron_logger.info("Checking block: %s", block_number)
                    block = tron.get_block(block_number)

                    if 'transactions' in block:
                        for tx in block['transactions']:
                            if tx['raw_data']['contract'][0]['type'] == 'TriggerSmartContract':
                                contract_address = to_base58check_address(
                                    tx['raw_data']['contract'][0]['parameter']['value']['contract_address']
                                )
                                if contract_address == usdt_contract_address:
                                    handle_event(tx, currency)
                    else:
                        tron_logger.info("No transactions found in block: %s", block_number)

                    last_seen_block = block_number
                    save_last_seen_block_number(last_seen_block)
                except BlockNotFound:
                    tron_logger.warning("Block %s not found, skipping", block_number)
                    continue
                except Exception as e:
                    tron_logger.error("Failed to process block %s: %s", block_number, e)
                    continue

            await asyncio.sleep(poll_interval)
        except asyncio.CancelledError:
            tron_logger.info("Log loop was cancelled. Exiting gracefully.")
            break
        except Exception as e:
            tron_logger.error("An error occurred: %s", e)
            traceback.print_exc()

def main():
    tron_logger.info("Starting ingestion for the TRON network")
    currency = {
        "name": "TRX/USDT",
        "contract_address": usdt_contract_address,
        "decimals": 6,  # USDT has 6 decimals on TRON
        "code": "USDT",
        "issuer": "TRON"
    }

    tasks = [log_loop(2, currency)]  # Set poll_interval to 2 seconds

    # Check if an event loop is already running
    try:
        loop = asyncio.get_running_loop()
        # If a loop is already running, add tasks to it
        for task in tasks:
            asyncio.ensure_future(task)
    except RuntimeError:
        # No loop is running; create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(*tasks))

if __name__ == "__main__":
    main()
