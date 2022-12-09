# Rail Bridge Server
This is a stand alone server written in python. It is designed to make connecting to the celo network as easy as possible. 
It allows you to be notified when a payment is received by a particular account. It also allows you to send a payment via a HTTP request.
It can be used by any project that needs to accept or send payments such as client wallets or banks making payouts.

Handles:

- Creating web3 transactions.
- Monitoring a celo based contracts.
## Downloading the server
Prebuilt binaries of the rail-server server are available on the for easy donwload and execction.

| Platform       | Binary file name                                                                         |
|----------------|------------------------------------------------------------------------------------------|
| Mac OSX 64 bit | [rail-darwin-amd64](https://github.com/stellar/rail-server/releases)      |
| Linux 64 bit   | [rail-linux-amd64](https://github.com/stellar/rail-server/releases)       |
| Windows 64 bit | [rail-windows-amd64.exe](https://github.com/stellar/rail-server/releases) |

Alternatively, you can [build](#building) the binary yourself.
## Config

The `.env` file must be present in a working directory. Here is an [example configuration file](https://github.com/stellar/rail-server/blob/master/example.env). env file should contain following values:

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

`Content-Type` of requests data should be `application/x-www-form-urlencoded`.

### GET /create-keypair

Creates a new random key pair.

#### Response

```json
{
    "address": "0x4ABC37F4E8147e4b06F39ff43114fA14faC4e530",
    "privateKey": "0x15da03f249e20eb80690eacf46bd13a32875fbc9992eb2700776e3e7e1eefb1a"
}
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
