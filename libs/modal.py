import jwt
from flask import jsonify, request
from urllib3.packages.six import wraps
from cryptography.fernet import Fernet

from config import SecretKey


class Modal:

    def __init__(self):
        self.app_key = "wKmeBgkVVMfDHP7aaLfAkhiuP6hdhR7isTPhr1O_IBk="

    def encrypt_info(self, message):
        fernet = Fernet(self.app_key)
        encMessage = fernet.encrypt(message.encode()).decode()
        return encMessage

    def decrypt_info(self, encMessage):
        fernet = Fernet(self.app_key)
        decMessage = fernet.decrypt(encMessage.encode()).decode()
        return decMessage

    @staticmethod
    def make_response(status, message, data=None):
        if data is None:
            rsp = {'status': status, 'message': message}
        else:
            rsp = {'status': status, 'message': message, "data": data}
        if status == 100:
            code = 200
        elif status == 404:
            code = 404
        else:
            code = 403
        return jsonify(rsp), code

    def get_abi(self):
        abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [
                    {
                        "name": "",
                        "type": "string"
                    }
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {
                        "name": "spender",
                        "type": "address"
                    },
                    {
                        "name": "tokens",
                        "type": "uint256"
                    }
                ],
                "name": "approve",
                "outputs": [
                    {
                        "name": "success",
                        "type": "bool"
                    }
                ],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [
                    {
                        "name": "",
                        "type": "uint256"
                    }
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {
                        "name": "from",
                        "type": "address"
                    },
                    {
                        "name": "to",
                        "type": "address"
                    },
                    {
                        "name": "tokens",
                        "type": "uint256"
                    }
                ],
                "name": "transferFrom",
                "outputs": [
                    {
                        "name": "success",
                        "type": "bool"
                    }
                ],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [
                    {
                        "name": "",
                        "type": "uint8"
                    }
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "_totalSupply",
                "outputs": [
                    {
                        "name": "",
                        "type": "uint256"
                    }
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {
                        "name": "tokenOwner",
                        "type": "address"
                    }
                ],
                "name": "balanceOf",
                "outputs": [
                    {
                        "name": "balance",
                        "type": "uint256"
                    }
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [
                    {
                        "name": "",
                        "type": "string"
                    }
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {
                        "name": "to",
                        "type": "address"
                    },
                    {
                        "name": "tokens",
                        "type": "uint256"
                    }
                ],
                "name": "transfer",
                "outputs": [
                    {
                        "name": "success",
                        "type": "bool"
                    }
                ],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {
                        "name": "tokenOwner",
                        "type": "address"
                    },
                    {
                        "name": "spender",
                        "type": "address"
                    }
                ],
                "name": "allowance",
                "outputs": [
                    {
                        "name": "remaining",
                        "type": "uint256"
                    }
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "name": "from",
                        "type": "address"
                    },
                    {
                        "indexed": True,
                        "name": "to",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "name": "tokens",
                        "type": "uint256"
                    }
                ],
                "name": "Transfer",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "name": "tokenOwner",
                        "type": "address"
                    },
                    {
                        "indexed": True,
                        "name": "spender",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "name": "tokens",
                        "type": "uint256"
                    }
                ],
                "name": "Approval",
                "type": "event"
            }
        ]
        return abi


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        print(kwargs)
        print(args)
        token = None
        if 'Authorization' in request.headers:
            sent_token = request.headers['Authorization']
            token = sent_token.replace("Bearer", "").strip()
        if not token:
            return jsonify({'message': 'a valid token is missing'})

        try:
            decoded = jwt.decode(token, SecretKey, algorithms="HS256")
            decoded_username = decoded['username']
            current_user = Modal.get_user_by_username(decoded_username)
        except:
            return jsonify({'message': 'token is invalid'})
        return f(current_user, *args, **kwargs)

    return decorator


modal = Modal()
if __name__ == '__main__':
    modal.upload_single_file()
