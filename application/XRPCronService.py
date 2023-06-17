import os
import asyncio
import ssl
from dotenv import load_dotenv
from xrpl.clients import WebsocketClient
from xrpl.models.transactions import Payment
from xrpl.wallet import Wallet
from xrpl.ledger import get_latest_validated_ledger_sequence

load_dotenv()

xrpl_ws = "wss://testnet.xrpl-labs.com"
address = "rJB2MGSEwZ3EfhxWKErwcFKxvVJjbSMePz"
secretKey = "ssC2spVyWwVrYYMy2Ni9CpaJtz3sT"
asset_issuer = "rUGX"
asset_code = "rNWY6caugMoE1Qa89ZBDM5TfgzWrw8Du32"

test_wallet = Wallet(seed=secretKey, sequence=16237283)

def process_received_data(payment: Payment):
    # Process the received data here
    print(f"Transaction: {payment}")
    print(f"Amount: {payment.amount.value}")
    print(f"Sender: {payment.account}")
    print(f"Destination: {payment.destination}")

    # For now, let's just print the transaction
    print(payment)

async def handle_incoming_payment(payment: Payment):
    if payment.destination == wallet.classic_address:
        if payment.amount.currency == asset_code and payment.amount.issuer == asset_issuer:
            process_received_data(payment)

async def listen_for_incoming_payments():
    async with WebsocketClient(xrpl_ws) as client:
        ledger_index = await get_latest_validated_ledger_sequence(client)
        print(f"Listening for payments starting from ledger {ledger_index}")
        while True:
            response = await client.send({
                "command": "subscribe",
                "accounts": [wallet.classic_address],
            })
            for transaction in response['result']['transactions']:
                if transaction['transaction']['TransactionType'] == 'Payment':
                    payment = Payment.from_dict(transaction['transaction'])
                    await handle_incoming_payment(payment)

            ledger_index += 1

async def main():
    await listen_for_incoming_payments()

if __name__ == "__main__":
    ssl._create_default_https_context = ssl._create_unverified_context
    asyncio.run(main())
