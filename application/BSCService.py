import asyncio
import json
import os
import ssl
import traceback
import logging
from dotenv import load_dotenv
from web3 import Web3
from web3._utils.events import get_event_data
from web3.middleware import geth_poa_middleware
from helpers.modal import Modal as md
from helpers.dbhelper import Database as Db

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
bsc_logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Connection to Binance Smart Chain network
provider_url = os.getenv("BSC_PROVIDER_URL")
web3 = Web3(Web3.WebsocketProvider(provider_url))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Verify connection
if web3.is_connected():
    bsc_logger.info("Connected to Binance Smart Chain WebSocket")
else:
    bsc_logger.error("Failed to connect to Binance Smart Chain WebSocket")
    exit(1)

# Load ABI from file
def load_abi(abi_file):
    with open(f"abi/{abi_file}", "r") as abi_file:
        return json.load(abi_file)

contract_address = Web3.to_checksum_address(os.getenv("BSC_CONTRACT_ADDRESS"))
bsc_logger.info(f"Using contract address: {contract_address}")

# Supported tokens with loaded ABIs
supported_tokens = [
    {
        "name": "cNGN",
        "contract_address": contract_address,
        "abi": load_abi(os.getenv("BSC_ABI_FILE")),
        "decimals": 6,
        "code": "cNGN",
        "issuer": contract_address,
    }
]

# Database functions
def save_last_seen_block_number(block_number):
    bsc_logger.info("Saving last seen block: %s", block_number)
    Db().Update("ChainBlock", "chain='bsc'", **{"last_seen_block": block_number})
    return True

def load_last_seen_block_number():
    db = Db()
    result = db.select("SELECT last_seen_block FROM ChainBlock WHERE chain = %s", ("bsc",))
    return int(result[0]["last_seen_block"]) if result else 0

def get_payment_addresses():
    db = Db()
    result = db.select("SELECT address FROM addresses WHERE chain='bsc' AND status='active'")
    return [row["address"] for row in result]

# Event processing
def handle_event(event, token):
    bsc_logger.info("Step 1: Received a new event.")

    # Decode the event using the contract ABI
    contract = web3.eth.contract(address=token["contract_address"], abi=token["abi"])
    transfer_event_abi = contract.events.Transfer._get_event_abi()

    try:
        bsc_logger.info("Step 2: Decoding the event using ABI.")
        decoded_event = get_event_data(web3.codec, transfer_event_abi, event)
        bsc_logger.info("Step 3: Event decoded successfully.")

        transaction_hash = decoded_event["transactionHash"]
        args = decoded_event["args"]

        bsc_logger.info("Step 4: Extracted transaction hash: %s", transaction_hash.hex())
        bsc_logger.info("Step 5: Extracted event arguments: %s", args)

        amount = args.get("value")
        to_address = args["to"]

        bsc_logger.info("Step 6: Extracted amount: %s", amount)
        bsc_logger.info("Step 7: Extracted recipient address: %s", to_address)

        payment_addresses = get_payment_addresses()

        normalized_to_address = to_address.lower()  # Convert to lowercase
        # Convert all payment addresses to lowercase
        normalized_payment_addresses = [addr.lower() for addr in payment_addresses]

        bsc_logger.info("Step 8: Retrieved payment addresses: %s", payment_addresses)

        if normalized_to_address in normalized_payment_addresses:
            bsc_logger.info("Step 9: Recipient address is in monitored addresses.")
            process_received_data(args, amount, token, transaction_hash)
        else:
            bsc_logger.info("Step 10: Recipient address not in monitored addresses: %s", to_address)

        return True
    except Exception as e:
        bsc_logger.error("Failed to decode event: %s", e)
        traceback.print_exc()
        return False

def process_received_data(args, amount, token, transaction_hash):
    try:
        bsc_logger.info("Processing transaction: %s", transaction_hash.hex())
        from_address = args["from"]
        to_address = args["to"]
        asset_amount = amount / (10 ** token["decimals"])

        # Log transaction details
        bsc_logger.info("Transaction details:")
        bsc_logger.info("Transaction Hash: %s", transaction_hash.hex())
        bsc_logger.info("From Address: %s", from_address)
        bsc_logger.info("To Address: %s", to_address)
        bsc_logger.info("Asset Amount: %.6f", asset_amount)
        bsc_logger.info("Currency Code: %s", token["code"])
        bsc_logger.info("Contract Address: %s", token["contract_address"])
        bsc_logger.info("Network: BSC")

        md.payout_callback(
            transaction_hash.hex(),
            to_address,
            from_address,
            asset_amount,
            token["code"],
            token["contract_address"],
            "BSC",""
        )
        return True
    except Exception as e:
        bsc_logger.error("Error while processing transaction: %s", e)
        traceback.print_exc()

# Main event loop using eth_getLogs with block range batching and hex prefix fix
async def log_loop(poll_interval, token):
    last_seen_block = load_last_seen_block_number()
    bsc_logger.info("Last checked block: %s", last_seen_block)

    while True:
        try:
            current_block_number = web3.eth.block_number
            bsc_logger.info("Current block number: %s", current_block_number)

            # Define the block batch size (based on BlastAPI limits)
            block_batch_size = 500

            # Process blocks in batches to avoid API limits
            while last_seen_block < current_block_number:
                from_block = last_seen_block + 1
                to_block = min(from_block + block_batch_size - 1, current_block_number)

                bsc_logger.info(f"Fetching logs from block {from_block} to {to_block}")

                # Set up filter params for this batch
                event_signature_hash = web3.to_hex(web3.keccak(text="Transfer(address,address,uint256)"))

                filter_params = {
                    "fromBlock": web3.to_hex(from_block),  # Convert to hex with 0x prefix
                    "toBlock": web3.to_hex(to_block),      # Convert to hex with 0x prefix
                    "address": Web3.to_checksum_address(token["contract_address"]),
                    "topics": [event_signature_hash],
                }

                # Fetch logs using eth_getLogs
                try:
                    logs = web3.eth.get_logs(filter_params)

                    for event in logs:
                        handle_event(event, token)

                    # Update last seen block after successful fetch
                    last_seen_block = to_block
                    save_last_seen_block_number(last_seen_block)

                except ValueError as e:
                    bsc_logger.error(f"Error fetching logs: {e}")
                    # In case of a rate limit or similar issue, wait before retrying
                    await asyncio.sleep(5)

            # Sleep before the next polling iteration
            await asyncio.sleep(poll_interval)

        except KeyboardInterrupt:
            bsc_logger.info("Interrupted by user, stopping...")
            break
        except Exception as e:
            bsc_logger.error("An error occurred: %s", e)
            traceback.print_exc()

async def main():
    bsc_logger.info("Starting ingestion for the BSC contract")

    ssl._create_default_https_context = ssl._create_unverified_context

    # Create log loops for each supported token
    tasks = [log_loop(1, token) for token in supported_tokens]
    await asyncio.gather(*tasks)