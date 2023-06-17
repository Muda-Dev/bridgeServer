import asyncio
import json
import os
import ssl
from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import BlockNotFound
from web3.middleware import geth_poa_middleware
from helpers.modal import Modal as md
from helpers.config import rpc_endpoints as rpc

load_dotenv()

rpc_endpoint = rpc['ETH']['provider']
supported_currencies = rpc['ETH']['supportedCurrencies']
storage_file = "eth_block_number.txt"  # Path to the storage file

web3 = Web3(Web3.WebsocketProvider(rpc_endpoint))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)


def load_last_processed_block_number():
    try:
        with open(storage_file, "r") as file:
            return int(file.read())
    except FileNotFoundError:
        return 0


def save_last_processed_block_number(block_number):
    with open(storage_file, "w") as file:
        file.write(str(block_number))


def handle_event(event, currency):
    try:
        print("..received a new event\n")
        print(event)
        call_back_url = os.getenv("callback_url")
        data_1 = Web3.toJSON(event)
        print(data_1)
        data = json.loads(data_1)
        address = data.get("address")
        hash = data["transactionHash"]

        args = data["args"]

        amount = args.get('tokens') or args.get('amount')
        process_received_data(args, amount, currency, call_back_url, hash)

    except Exception as e:
        print("Something went wrong!!")
        print(e)


def process_received_data(args, amount, currency, call_back_url, hash):
    account_number = args["account_number"]
    webhook_url = args["webhook"]
    service_id = args["service_id"]
    decimals = currency.get('decimals', 1)
    pay_load = {
        "amount": amount / decimals,
        "tx_hash": hash,
        "service_id": service_id,
        "account_number": account_number,
    }
    print("callback url\n", call_back_url)
    print("sending payload", pay_load)
    response = md.send_post_request(pay_load, call_back_url)
    print(response)
    return True


async def log_loop(event_filter, poll_interval, currency):
    last_processed_block = load_last_processed_block_number()

    while True:
        try:
            current_block_number = web3.eth.block_number
            if last_processed_block < current_block_number:
                for block_number in range(last_processed_block + 1, current_block_number + 1):
                    try:
                        block = web3.eth.get_block(block_number)
                        for transaction in block.transactions:
                            receipt = web3.eth.get_transaction_receipt(transaction.hex())
                            for event in event_filter.get_all_entries():
                                if event['transactionHash'] == transaction.hex():
                                    handle_event(event, currency)
                                    break

                        last_processed_block = block_number
                        save_last_processed_block_number(last_processed_block)
                    except BlockNotFound:
                        pass
            await asyncio.sleep(poll_interval)

        except KeyboardInterrupt:
            break


def main():
    print("Starting ingestion for the cUGX contract")
    event_filters = []
    for currency in supported_currencies:
        contract_address = currency['contract_address']
        contract_abi = currency['abiFile']
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)
        event_filter = contract.events.Pay.createFilter(fromBlock='latest')
        event_filters.append((event_filter, currency))

    loop = asyncio.get_event_loop()
    try:
        tasks = [log_loop(event_filter, 2, currency) for event_filter, currency in event_filters]
        loop.run_until_complete(asyncio.gather(*tasks))
    finally:
        loop.close()


if __name__ == "__main__":
    ssl._create_default_https_context = ssl._create_unverified_context
    main()
