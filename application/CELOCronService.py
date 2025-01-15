import asyncio
import json
import os
import ssl
import traceback
import logging
from dotenv import load_dotenv
from web3 import Web3
from web3._utils.events import get_event_data
from web3.exceptions import BlockNotFound
from web3.middleware import geth_poa_middleware
from helpers.modal import Modal as md
from helpers.dbhelper import Database as Db

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
celo_logger = logging.getLogger(__name__)

# load_dotenv(env_file)

# Connection to Celo network
provider_url = os.getenv("CELO_PROVIDER_URL")
web3 = Web3(Web3.WebsocketProvider(provider_url))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)


# Load ABI from file
def load_abi(abi_file):
    with open(f"abi/{abi_file}", "r") as abi_file:
        return json.load(abi_file)


# Supported currencies with loaded ABIs
supported_currencies = [
    {
        "name": "cUSD",
        "contract_address": os.getenv("CELO_CONTRACT_ADDRESS"),
        "abi": load_abi(os.getenv("CELO_ABI_FILE")),
        "decimals": 18,
        "code": "cUSD",
        "issuer": os.getenv("CELO_CONTRACT_ADDRESS"),
    }
]


# Database functions
def save_last_seen_block_number(block_number):
    print("savedBlock", block_number)
    Db().Update("ChainBlock", "chain='celo'", **{"last_seen_block": block_number})
    return True


def load_last_seen_block_number():
    db = Db()
    result = db.select(
        "SELECT last_seen_block FROM ChainBlock WHERE chain = %s", ("celo",)
    )
    return int(result[0]["last_seen_block"]) if result else 0


def get_payment_addresses():
    db = Db()
    result = db.select("SELECT address FROM addresses WHERE chain='CELO' AND status='active'")
    return [row["address"] for row in result]


# Event processing
def handle_event(event, currency):
    celo_logger.info("Step 1: Received a new event.")

    # Decode the event using the contract ABI
    contract = web3.eth.contract(
        address=currency["contract_address"], abi=currency["abi"]
    )
    transfer_event_abi = contract.events.Transfer._get_event_abi()
    try:
        celo_logger.info("Step 2: Decoding the event using ABI.")
        decoded_event = get_event_data(web3.codec, transfer_event_abi, event)
        celo_logger.info("Step 3: Event decoded successfully.")

        transaction_hash = decoded_event["transactionHash"]
        args = decoded_event["args"]

        celo_logger.info("Step 4: Extracted transaction hash: %s", transaction_hash.hex())
        celo_logger.info("Step 5: Extracted event arguments: %s", args)

        amount = args.get("value")
        to_address = args["to"]

        celo_logger.info("Step 6: Extracted amount: %s", amount)
        celo_logger.info("Step 7: Extracted recipient address: %s", to_address)

        payment_addresses = get_payment_addresses()
        celo_logger.info("Step 8: Retrieved payment addresses: %s", payment_addresses)

        if to_address in payment_addresses:
            celo_logger.info("Step 9: Recipient address is in monitored addresses.")
            process_received_data(args, amount, currency, transaction_hash)
        else:
            celo_logger.info("Step 10: Recipient address not in monitored addresses: %s", to_address)

        return True
    except Exception as e:
        celo_logger.error("Failed to decode event: %s", e)
        traceback.print_exc()
        return False


def process_received_data(args, amount, currency, transaction_hash):
    try:
        celo_logger.info("Processing transaction: %s", transaction_hash.hex())
        from_address = args["from"]
        to_address = args["to"]
        asset_amount = amount / (10 ** currency["decimals"])

        # Log the transaction details
        celo_logger.info("Transaction details:")
        celo_logger.info("Transaction Hash: %s", transaction_hash.hex())
        celo_logger.info("From Address: %s", from_address)
        celo_logger.info("To Address: %s", to_address)
        celo_logger.info("Asset Amount: %.6f", asset_amount)
        celo_logger.info("Currency Code: %s", currency["code"])
        celo_logger.info("Contract Address: %s", currency["contract_address"])
        celo_logger.info("Network: celo")

        md.payout_callback(
            transaction_hash.hex(),
            to_address,
            to_address,
            asset_amount,
            currency["code"],
            currency["contract_address"],
            "celo",
        )
        return True
    except Exception as e:
        celo_logger.error("Error while processing transaction: %s", e)
        traceback.print_exc()


# Main event loop
async def log_loop(event_filter, poll_interval, currency):
    last_seen_block = load_last_seen_block_number()
    celo_logger.info("Last checked block: %s", last_seen_block)

    while True:
        try:
            current_block_number = web3.eth.block_number
            celo_logger.info("Current block number: %s", current_block_number)

            for block_number in range(last_seen_block + 1, current_block_number + 1):
                try:
                    celo_logger.info("Checking block: %s", block_number)
                    block = web3.eth.get_block(block_number, full_transactions=True)
                    for transaction in block.transactions:
                        receipt = web3.eth.get_transaction_receipt(transaction.hash)
                        transfer_events = receipt["logs"]
                        for event in transfer_events:
                            if (
                                event["address"].lower()
                                == currency["contract_address"].lower()
                            ):
                                handle_event(event, currency)
                    last_seen_block = block_number
                    save_last_seen_block_number(last_seen_block)
                except BlockNotFound:
                    continue

            await asyncio.sleep(poll_interval)
        except KeyboardInterrupt:
            celo_logger.info("Interrupted by user, stopping...")
            break
        except Exception as e:
            celo_logger.error("An error occurred: %s", e)
            traceback.print_exc()


def main():
    celo_logger.info("Starting ingestion for the Celo contract")
    last_seen_block = load_last_seen_block_number()
    event_filters = []
    for currency in supported_currencies:
        contract = web3.eth.contract(
            address=currency["contract_address"], abi=currency["abi"]
        )
        event_filter = contract.events.Transfer.create_filter(fromBlock=last_seen_block)
        event_filters.append((event_filter, currency))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = [
        log_loop(event_filter, 1, currency) for event_filter, currency in event_filters
    ]
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()


if __name__ == "__main__":
    ssl._create_default_https_context = ssl._create_unverified_context
    main()
