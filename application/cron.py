from audioop import add
from email.headerregistry import Address
import imp
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
from helpers.modal import Modal as md
load_dotenv()


rpc_endpoint = cfg['provider']
ugx_contract = md().get_contract("ugx")
usd_contract = md().get_contract("usd")

web3 = Web3(Web3.WebsocketProvider(rpc_endpoint))


#  address and abi
cugx_contract_address_abi = ugx_contract[0]
cusd_contract_address_abi = usd_contract[0]

cugx_contract_address = ugx_contract[1]['contract_address']
cusd_contract_address = usd_contract[1]['contract_address']


cugx_contract = web3.eth.contract(
    address=cugx_contract_address, abi=cugx_contract_address_abi)
cusd_contract = web3.eth.contract(
    address=cusd_contract_address, abi=cusd_contract_address_abi)

# define function to handle events and print to the console


def handle_event(event):
    try:
        print("..received a new event\n")
        # and whatever
        print(event)
        call_back_url = os.getenv("callback_url")
        data_1 = Web3.toJSON(event)
        print(data_1)
        data = json.loads(data_1)
        address = data.get("address")
        hash = data["transactionHash"]

        args = data["args"]
        response = []

        if address == cfg.get("cugx_contract_address"):
            # this is our contract transaction
            amount = args['tokens']
            account_number = args["account_number"]
            webhook_url = args["webhook"]
            service_id = args["service_id"]
            pay_load = {
                "amount": amount/100,
                "tx_hash": hash,
                "service_id": service_id,
                "account_number": account_number,
            }
            print("callback url\n", call_back_url)
            print("sending payload", pay_load)
            response = md.send_post_request(pay_load, call_back_url)

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
            # convert this to local currency
        else:
            print("received un supported event")
        print("callback response", response)

        if response.status_code == 200:
            response_json = response.json()
            print("callback response", response_json)
            client_pay_load = {
                "status": "success",
                "tx_hash": hash,
                "provider_trans_id": response_json['trans_id'],
                "account_number": account_number,
                "sent_amount": response_json['sent_amount']
            }
            print("transaction marked as successful")
            # tx is a success
            #send webook to client
            rsp = md.send_post_request(client_pay_load, webhook_url)
            print(rsp)
            print("client success message sent ", client_pay_load)
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


        print("sending call request to call back url, "+os.getenv("callback_url"))
    except Exception as e:
        print("something went wrong!!")
        print(e)


async def log_loop(event_filter, poll_interval):
    while True:
        blockNumber = web3.eth.get_block_number()
        print("blockNumber", blockNumber)
        for Transfer in event_filter.get_new_entries():
            handle_event(Transfer)
        await asyncio.sleep(poll_interval)


def main():
    print("starting ingestion for the cUGX contract")
    event_filter = cugx_contract.events.Pay.createFilter(fromBlock='latest')
    #event_filter_2 = cusd_contract.events.TransferComment.createFilter(fromBlock='latest')
    # tx_filter = web3.eth.filter('pending')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop(event_filter, 2)))
        #loop.run_until_complete(asyncio.gather(log_loop(event_filter_2, 2)))
    finally:
        loop.close()


if __name__ == "__main__":
    ssl._create_default_https_context = ssl._create_unverified_context
    main()
