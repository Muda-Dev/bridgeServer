import requests
import json
from web3 import Web3

from helpers.modal import get_exchange_rates,save_log,update_log


update_log('1234', json.dumps({'data': 'test'}))
# rates = get_exchange_rates(1000, 'CNGN', 'UGX')
# print(rates)

def getabi():
    # BscScan API Key (Replace with your own)
    bscscan_api_key = ''  # Add your API key here

    # Implementation contract address you retrieved
    impl_address = '0xFD4b3d9DeE82cA25592C4c57c796dD0E26d63208'

    # BscScan API URL to get contract ABI
    url = f"https://api.bscscan.com/api?module=contract&action=getabi&address={impl_address}&apikey={bscscan_api_key}"

    # Fetch ABI
    response = requests.get(url)
    data = response.json()

    if data['status'] == '1':
        contract_abi = json.loads(data['result'])  # Convert ABI string to JSON
        print(f"Contract ABI for {impl_address} fetched successfully.")

        # Save ABI to cngn.json
        with open('cngn.json', 'w') as abi_file:
            json.dump(contract_abi, abi_file, indent=4)
        print("ABI saved to cngn.json.")

        # Optional: Load into Web3 contract object
        w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
        contract = w3.eth.contract(address=impl_address, abi=contract_abi)

    else:
        print(f"Error fetching ABI: {data['result']}")
