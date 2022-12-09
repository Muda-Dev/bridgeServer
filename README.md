# bridge-server
This is a stand alone server written in python. It is designed to make connecting to the celo network as easy as possible. 
It allows you to be notified when a payment is received by a particular account. It also allows you to send a payment via a HTTP request.
It can be used by any project that needs to accept or send payments such as client wallets or banks making payouts.

Handles:

- Creating web3 transactions.
- Monitoring a celo based contracts.
## Downloading the server
Prebuilt binaries of the bridge-server server are available on the for easy donwload and execction.

| Platform       | Binary file name                                                                         |
|----------------|------------------------------------------------------------------------------------------|
| Mac OSX 64 bit | [bridge-darwin-amd64](https://github.com/stellar/bridge-server/releases)      |
| Linux 64 bit   | [bridge-linux-amd64](https://github.com/stellar/bridge-server/releases)       |
| Windows 64 bit | [bridge-windows-amd64.exe](https://github.com/stellar/bridge-server/releases) |

Alternatively, you can [build](#building) the binary yourself.
## Config

The `.env` file must be present in a working directory. Here is an [example configuration file](https://github.com/stellar/bridge-server/blob/master/example.env). env file should contain following values:

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

After creating `bridge.cfg` file, you need to run DB migrations:
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

### POST /create-keypair

Creates a new random key pair.

#### Response

```json
{
    "address": "0x4ABC37F4E8147e4b06F39ff43114fA14faC4e530",
    "privateKey": "0x15da03f249e20eb80690eacf46bd13a32875fbc9992eb2700776e3e7e1eefb1a"
}
```

### POST /payment

Creates a new transaction.
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




