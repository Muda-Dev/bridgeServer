import os
from dotenv import load_dotenv
load_dotenv()

stage = {
    "cusd_address": "",
    "cugx_address": "",
    "rpc_endpoint": "https://alfajores-forno.celo-testnet.org",
    "provider": "wss://alfajores-forno.celo-testnet.org/ws",
    "chain_id": 44787,
    "cugx_contract_address": "0xF17DB59dA5ddc58E08de2AD83478391Ab9797d50",
    "cugx_abi":"abi/cugx_abi_stage.json",
    "cusd_contract_address": "0xF17DB59dA5ddc58E08de2AD83478391Ab9797d50",
    "cusd_abi":"abi/cusd_abi_stage.json",
    "gas": 70000,
    "gasPrice": 50
}

prod = {
    "cusd_address": "",
    "cugx_address": "",
    "rpc_endpoint": "https://alfajores-forno.celo-testnet.org",
    "provider": "wss://alfajores-forno.celo-testnet.org/ws",
    "chain_id": 44787,
    "cugx_contract_address": "0xF17DB59dA5ddc58E08de2AD83478391Ab9797d50",
    "cugx_abi":"abi/cugx_abi_stage.json",
    "cusd_contract_address": "0xF17DB59dA5ddc58E08de2AD83478391Ab9797d50",
    "cusd_abi":"abi/cusd_abi_stage.json",
    "gas": 70000,
    "gasPrice": 50
}

if os.getenv("mode") == "live":
    config = prod
else:
    config = stage
