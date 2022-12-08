from audioop import add
import json
from web3 import Web3
import asyncio
import os
import json
from helpers.modal import Modal as md
import ssl
from flask import jsonify
from dotenv import load_dotenv
from config import config as cfg
load_dotenv()


rpc_endpoint = cfg['provider']
web3 = Web3(Web3.WebsocketProvider(rpc_endpoint))
cugx_contract_address = cfg['cugx_contract_address']
cusd_contract_address = cfg['cusd_contract_address']

cugx_abi = cfg['cugx_abi']
cusd_abi = cfg['usd_abi']

with open(cugx_abi) as f:
    cugx_data = json.load(f)
with open(cusd_abi) as f:
    cusd_data = json.load(f)

#  address and abi
cugx_contract_address_abi = cugx_data
cusd_contract_address_abi = cusd_data

cugx_contract = web3.eth.contract(address=cugx_contract_address, abi=cugx_contract_address_abi)
cusd_contract = web3.eth.contract(address=cusd_contract_address, abi=cusd_contract_address_abi)


# define function to handle events and print to the console
def handle_event(event):
    try:
        print("..received a new event\n")
        # and whatever
        call_back_url = os.getenv("callback_url")
        data_1 = Web3.toJSON(event)
        data = json.loads(data_1)
        address = data.get("address")
        hash = data["transactionHash"]
        account_number = ""
        webhook_url = ""
        args = data["args"]
        if address == cfg.get("cugx_contract_address"):
            # this is our contract transaction
            amount = args['tokens']

        elif address == cfg.get("cusd_contract_address"):
            # this is a cusd transaction
            amount = args['amount']
            pay_load = {
                "amount": amount/100,
                "tx_hash": hash,
                "account_number": account_number,
            }
            print("callback url\n", call_back_url)
            print("sending payload", pay_load)

            response = md.send_post_request(pay_load, call_back_url)
            if response.status_code == 200:
                response_json = response.json()
                client_pay_load = {
                    "status": "success",
                    "tx_hash": hash,
                    "provider_trans_id": response_json['trans_id'],
                    "account_number": account_number,
                    "sent_amount": response_json['sent_amount']
                }
                print("transaction marked as successful")
                # tx is a success
                rsp = md.send_post_request(client_pay_load, webhook_url)
                print("client success message sent, "+client_pay_load)
            else:
                #tx is not processed
                response_json = response.json()
                client_pay_load = {
                    "status": "failed",
                    "error": response_json['error'],
                    "provider_trans_id": "",
                    "account_number": account_number,
                    "sent_amount": ""
                }
                print("transaction marked as successful")
                # tx is a success
                rsp = md.send_post_request(client_pay_load, webhook_url)
                print("client error message sent, "+client_pay_load)

            # convert this to local currency
        else:
            print("received un supported event")

        print("sending call request to call back url, "+os.getenv("callback_url"))
    except Exception as e:
        print("something went wrong!!")
        print(e)


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the "Transfer" event
# this loop runs on a poll interval
async def log_loop(event_filter, poll_interval):
    while True:
        print("here", event_filter)
        for Transfer in event_filter.get_new_entries():
            handle_event(Transfer)
        await asyncio.sleep(poll_interval)


# when main is called
# create a filter for the latest block and look for the "Transfer" event for the  factory contract
# run an async loop
# try to run the log_loop function above every 2 seconds
def main():
    print("starting ingestion")
    event_filter = cugx_contract.events.Transfer.createFilter(fromBlock='latest')
    event_filter_2 = cusd_contract.events.Transfer.createFilter(fromBlock='latest')
    #block_filter = web3.eth.filter('latest')
    # tx_filter = web3.eth.filter('pending')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop(event_filter, 2)))
        loop.run_until_complete(asyncio.gather(log_loop(event_filter_2, 2)))
        # log_loop(tx_filter, 2)))
    finally:
        # close loop to free up system resources
        loop.close()


if __name__ == "__main__":
    ssl._create_default_https_context = ssl._create_unverified_context
    main()
