import os
from dotenv import load_dotenv
load_dotenv()

currencies=["ugx","usd"]
stage = {
    "cugx_contract_address":"0xF17DB59dA5ddc58E08de2AD83478391Ab9797d50",
    "cusd_contract_address":"0xF17DB59dA5ddc58E08de2AD83478391Ab9797d50",
    "rpc_endpoint": "https://alfajores-forno.celo-testnet.org",
    "provider": "wss://alfajores-forno.celo-testnet.org/ws",
    "chain_id": 44787,
    "cugx_contract": {
        "contract_address": "0xF17DB59dA5ddc58E08de2AD83478391Ab9797d50",
        "abi": "abi/cugx_abi_stage.json",
        "decimals": 100,
        "coin": "cugx"
    },
    "cusd_contract": {
        "contract_address": "0xF17DB59dA5ddc58E08de2AD83478391Ab9797d50",
        "abi": "abi/cusd_abi_stage.json",
        "coin": "cusd",
        "decimals": 1000000000000000000
    },
    "gas": 70000,
    "gasPrice": 50
}

prod = {
    
}

if os.getenv("mode") == "live":
    config = prod
else:
    config = stage
