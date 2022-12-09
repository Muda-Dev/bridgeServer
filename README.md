# Bridge Server

Bridge is a Python api for creating and submitting transaction to the CELO blockchain. This service should be cloned and run by client wallets that wish to be part of the MUDA Liquidity Rail eco-system.

## Overview
The Bridge Server is web3 abstraction api service that allows developers to use web3 without the need to learn about blockchain. It provides a basic blockhain based operations that are needed by clients to make payments, interact with contracts etc.
#### Supported Opeartions
- Check balances
- Send Payments(Contract calls)
- Check account history
- Get Transaction id(hash)
- Prives a Service api to MUDA Liquidity Rail service providers



## Installation
Clone this repo and use the package manager [pip3](https://pip.pypa.io/en/stable/) to install depencies

```bash
pip3 install -r requirements.txt
```

## Usage

```python
python3 run.py
```
Open the browser and check [http://localhost:8002](http://localhost:8002).
Once the server is running, check the [API Documentation](https://documenter.getpostman.com/view/3143535/U16nKirS) and start your local intergration.  Use http://localhost:8002/ as your base API Endpoint.


## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)