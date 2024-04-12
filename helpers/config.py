import os
from dotenv import load_dotenv
from helpers.contracts import config as cfg
load_dotenv()

version="1.0.0"
db="db_1.sql"
service_url = "https://muda-dev.github.io/Liqudity-Rail/services.json"


# RPC endpoints for different chains. These need to be added into a database in the near future.
rpc_endpoints = {
    "ETH": {
        "url": "https://mainnet.infura.io/v3/your-infura-project-id",
        "provider": "wss://alfajores-forno.celo-testnet.org/ws",
        "chain_id": 1,
        "supportedCurrencies": [
            {
                "asset": "USDC",
                "contract_address": "0x82532B034275CFf660044a0728b5d91Bad1704d1",
                "abiFile": cfg['eth_usdc']
            }
        ]
    },
    "CELO": {
        "url": "https://alfajores-forno.celo-testnet.org",
        "provider": "wss://alfajores-forno.celo-testnet.org/ws",
        "chain_id": 44787,
        "supportedCurrencies": [
            {
                "asset": "CUGX",
                "contract_address": "0x82532B034275CFf660044a0728b5d91Bad1704d1",
                "abiFile": cfg['celo_cugx']
            }

        ]
    },

    "XRP": {
        "url": "https://s.altnet.rippletest.net:51234/",
        "provider": "",
        "chain_id": "",
        "supportedCurrencies": [
            {
                "asset": "xUGX",
                "contract_address": "rUvSzZ81jtbTBwuMpBEExzQCooYL7xQfmj",  # asset issuer
                "abiFile": ""
            }
        ]
    },
}


# Other configuration parameters
DEBUG = os.getenv("DEBUG") == "True"
PORT = int(os.getenv("PORT"))
HOST_NAME = os.getenv("HOST_NAME")
USER_NAME = os.getenv("USER_NAME")
PASSWORD = os.getenv("PASSWORD")
DBNAME = os.getenv("DBNAME")
mode = os.getenv("mode")
currency = os.getenv("currency")
callback_url = os.getenv("callback_url")
webhook_url = os.getenv("webhook_url")
enc_key = os.getenv("enc_key")
address = os.getenv("address")
