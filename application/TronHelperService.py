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
from tronpy.keys import to_base58check_address

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Tron API keys for rotation
API_KEYS = [
    "61487e05-52a3-4da0-a9fd-db0d9353b03d",
    "c7ecb219-8949-447f-816a-d28aa562e303",
    # Add more keys as needed
]
current_key_index = 0

def get_next_api_key():
    global current_key_index
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return key

def get_tron_client():
    return Tron(HTTPProvider(api_key=get_next_api_key()))

tron = get_tron_client()

# USDT contract address on TRON
usdt_contract_address = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'

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
    return int(result[0]["last_seen_block"]) if result else 0

def get_payment_addresses():
    db = Db()
    result = db.select("SELECT address FROM addresses WHERE chain='TRX' and status='active'")
    return [row["address"] for row in result]

# Event processing
def handle_event(transaction, currency):
    logger.info("Received a new event: %s", transaction)

    try:
        transaction_hash = transaction['txID']  # Corrected key
        raw_data = transaction['raw_data']['contract'][0]['parameter']['value']
        
        # Extract and convert addresses
        owner_address = to_base58check_address(raw_data.get("owner_address"))
        contract_address = to_base58check_address(raw_data.get("contract_address"))
        amount = int(raw_data.get("data", "0"), 16)  # Convert hex data to integer
        
        # Check if the transaction is for a monitored contract
        if contract_address != currency['contract_address']:
            logger.info("Ignoring transaction for unrelated contract: %s", contract_address)
            return False

        # Get payment addresses from DB
        payment_addresses = get_payment_addresses()
        if owner_address in payment_addresses:
            process_received_data(raw_data, amount, currency, transaction_hash)
        else:
            logger.info("Owner address not in monitored addresses: %s", owner_address)
        return True
    except Exception as e:
        logger.error("Failed to process event: %s", e)
        traceback.print_exc()
        return False
        
def process_received_data(args, amount, currency, transaction_hash):
    try:
        logger.info("Processing transaction: %s", transaction_hash)
        from_address = to_base58check_address(args.get("owner_address"))
        to_address = to_base58check_address(args.get("to_address"))
        asset_amount = amount / (10 ** currency["decimals"])
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
        logger.error("Error: %s", e)
        traceback.print_exc()

# Main event loop
async def log_loop(poll_interval, currency):
    last_seen_block = load_last_seen_block_number()
    logger.info("Last checked block: %s", last_seen_block)

    while True:
        try:
            current_block_number = tron.get_latest_block_number()
            logger.info("Current block number: %s", current_block_number)

            for block_number in range(last_seen_block + 1, current_block_number + 1):
                try:
                    logger.info("Checking block: %s", block_number)
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
                        logger.info("No transactions found in block: %s", block_number)
                    
                    last_seen_block = block_number
                    save_last_seen_block_number(last_seen_block)
                except BlockNotFound:
                    logger.warning("Block %s not found, skipping", block_number)
                    continue
                except Exception as e:
                    logger.error("Failed to process block %s: %s", block_number, e)
                    continue

            await asyncio.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Interrupted by user, stopping...")
            break
        except Exception as e:
            logger.error("An error occurred: %s", e)
            traceback.print_exc()

def main():
    logger.info("Starting ingestion for the TRON network")
    currency = {
        "name": "TRX/USDT",
        "contract_address": usdt_contract_address,
        "decimals": 6,  # USDT has 6 decimals on TRON
        "code": "USDT",
        "issuer": "TRON"
    }

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = [log_loop(2, currency)]  # Set poll_interval to 2 seconds
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("The 'dotenv' module is not installed. Environment variables will not be loaded from a .env file.")
    main()
