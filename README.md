# Rail Bridge Server
The Rail Bridge Server is a standalone server implemented in Python. It's designed to simplify connections to the Web3 network. The server enables you to receive notifications when a specific account receives a payment, and also permits sending payments via HTTP requests. It can be adopted by any project needing to accept or send payments such as client wallets or banks executing payouts.

The server is capable of:
- Creating Web3 transactions.
- Monitoring Web3-based contracts.
- Monitoring XRP asset transactions.

## Service Providers
Service providers are organizations/companies offering end-user services like money transfers, utility payments like airtime, water payments, etc. To send transactions as a client, you will require a service ID. We maintain an open list of all service providers [here](https://github.com/Muda-Dev/Liqudity-Rail/blob/main/services.json). You can also access the services as a JSON endpoint [here](https://muda-dev.github.io/Liqudity-Rail/services.json).

## Supported Block Chains
1. [CELO](https://celo.org/)
2. [ETHEREUM](https://ethereum.org/)
3. [XRP](https://ripple.com/currency/)

## Downloading the Server
Prebuilt binaries of the Rail Bridge Server are available for easy download and execution.

| Platform       | Binary File Name                                                                         |
|----------------|------------------------------------------------------------------------------------------|
| Mac OSX 64 bit | [rail-darwin-amd64](https://github.com/Muda-Dev/Liqudity-Rail/blob/main/release/mac.zip)      |
| Linux 64 bit   | [rail-linux-amd64](https://github.com/Muda-Dev/Liqudity-Rail/blob/main/release/mac.zip)       |
| Windows 64 bit | [rail-windows-amd64.exe](https://github.com/Muda-Dev/Liqudity-Rail/blob/main/release/mac.zip) |

Alternatively, you can [build](#building) the binary yourself.
## Config

The `.env` file must be present in a working directory. Here is an [example configuration file](https://github.com/Muda-Dev/Liqudity-Rail/blob/main/release/example.env). env file should contain following values:

* `port` - server listening port
* `address` - this is the address that will be receiving payments
* `pay_account_private_key` - This is your web3 private key that will be used to make out going payments.
* `callback_url` - URL that will be called when a new payment has been received.
* `webhook_url` - URL which will receive payment notifications from service providers once a transaction has been completed.
* `currency` - currency that you transact in. Currently this is one of ugx and usd
* `database`
  * `HOST_NAME` - by default it's localhost
  * `USER_NAME` - your database username
  * `PASSWORD` - your database password
  * `DBNAME` - your database name
* `mode` - this is one of [dev,test,live] this setting tells which network the service is going to use
* `enc_key` - encryption key that will be used to sign your callbacks

## Getting started

After creating `rail.cfg` file, you need to run DB migrations:
```
./rail --migrate-db
```
## Running the service as a client

 Start the server with a client arg:
```
./rail provider client
```
## Client API

`Content-Type` of requests data should be `application/json`.

### GET /create-keypair

Creates a new random key pair.

#### Response

```json
[
    {
        "EVM": {
            "address": "0x841d0DE13f5c154CbfF616b00020A9B419b145de",
            "privateKey": "0xe3b5921f99dcf2636af58578d8ffb95bae30b6d33843aca137a5a5da66181b54"
        }
    },
    {
        "XRP": {
            "classic_address": "r4gc1C95hGRJbFYA78QmrKqv5Vv8e3Unop",
            "seed": "sEdV3ReWzgqeqEMsgbTcCsrgT97EgW7"
        }
    }
]
```

### POST /payment

Creates a new transaction and uses the private key set in your .env file to sign the transaction.
```json
{
    "amount": 10,
    "recipient": "0xb1aa591c8Ef1c2b1AFA361ed10E3E6bA845c4bf4",
    "sending_token": "cUSD",
    "extra_data": {
        "service_id": 1,
        "account_number": "+256700000000"
    }
}
```
#### Response

```json
{
    "message": {
        "amount": 10,
        "contract_address": "0x82532B034275CFf660044a0728b5d91Bad1704d1",
        "currency": "usd",
        "txHash": "0x3878c4a1080148901f6c6590ae003239995add843efdb2e0d638371c64a9a998"
    },
    "status": 100
}
```
### GET /get_linked_address

Get's the address set in your .env file

#### Response

```json
{
    "address": "0xF968575Dc8872D3957E3b91BFAE0d92D4c9c1Dd5"
}
```
### GET /get_balance

Get's the balance of the address set in your .env file

#### Response

```json
{
    "balance": 100000000,
    "asset": "cUGX",
    "contract_address": "0xF968575Dc8872D3957E3b91BFAE0d92D4c9c1Dd5"
}
```

## Running the service as a client

 Start the server with a client arg:
```
./rail provider service
```
The server will start a blockchain listeing service which will listen for events emitted by the contract. Once a new payment is received, a callback will be sent to the callback url.

## Callbacks

The Rail server listens for payment operations to the account specified in the .env file ad address. Every time 
a payment arrives it will send a HTTP POST request to callback_url endpoint.
`Content-Type` of requests data will be `application/json`.

### POST callback_url

A POST request will be sent to the callback url set in the .env file.
name | description
--- | ---
`tx_hash` | Transaction hash from the blockchain
`amount` | amount recived from the transaction
`service_id` | service_id received from the emited even
`account_number` | account_number received from the emited even

#### Request

```json
{
    "amount": 100000,
    "tx_hash": "0x3878c4a1080148901f6c6590ae003239995add843efdb2e0d638371c64a9a998",
    "service_id": 1,
    "account_number": "256787700000",
}
```
#### Response
```json
{
    "sent_amount": 100000,
    "trans_id": "124567890",
}
```

Respond with `200 OK` when processing succeeded. Any other status code will be considered an error and rail server will keep sending this payment request again and will not continue to next payments until it receives `200 OK` response.

## Webhook

Once a transaction has been sent to the callback endpoitn and a service has been issued to the sender, the rail server will send a webhook to the client notifying them of the finak status of the transastion. The webhook URL

`Content-Type` of requests data will be `application/json`.
#### Request
name | description
--- | ---
`status` | send success or failed
`tx_hash` | Transaction hash from the blockchain
`sent_amount` | amount paid to the account number provided
`account_number` | account that received the transaction
`provider_trans_id` | Transaction from the servive providers platform

```json
{
    "status": "success",
    "tx_hash": "0x3878c4a1080148901f6c6590ae003239995add843efdb2e0d638371c64a9a998",
    "provider_trans_id": "124567890",
    "account_number": "256787700000",
    "sent_amount": "100000"
}
```
#### Response
Respond with `200 OK` when processing succeeded. Any other status code will be considered an error and rail server will keep sending this payment request again and will not continue to next payments until it receives `200 OK` response.

## Building

python3 is used for building and testing.

Given you have a running python installation, you can start by installing depencies with pip3:

```
pip3 install -r requirements.txt
```

After a successful installation, you should run the app with.

## Running as a service provider
```
python3 run.py provider service
```
## Running as a client
```
python3 run.py provider client
```
Then simply open:
```
http://localhost:8001
```
in a browser.
