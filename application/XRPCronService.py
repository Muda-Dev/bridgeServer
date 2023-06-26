import asyncio
import websockets
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def handler(websocket):
    message = await websocket.recv()
    return message

async def api_request(options, websocket):
    try:
        await websocket.send(json.dumps(options))
        message = await websocket.recv()
        return json.loads(message)
    except Exception as e:
        return e

async def pingpong(websocket):
    command = {
        "id": "on_open_ping_1",
        "command": "ping"
    }
    value = await api_request(command, websocket)
    print(value)

async def do_subscribe(websocket):
    command = await api_request({
        'command': 'subscribe',
        'accounts': [os.getenv("address")]
    }, websocket)

    if command.get('status') == 'success':
        print('Successfully Subscribed!')
    else:
        print("Error subscribing: ", command)
    print('Received message from server', await handler(websocket))

def onTransactionReceived(transaction):
    # Extract transaction details
    tx_type = transaction.get('type')
    tx_from = transaction.get('account')
    tx_to = transaction.get('destination')
    tx_amount = transaction.get('amount')
    tx_asset = transaction.get('currency')
    tx_memo = transaction.get('memos')

    # Print transaction details
    print("Received transaction:")
    print(f"Type: {tx_type}")
    print(f"From: {tx_from}")
    print(f"To: {tx_to}")
    print(f"Amount: {tx_amount}")
    print(f"Asset: {tx_asset}")
    print(f"Memo: {tx_memo}")
    print("--------------------")
    # send this to my service. TODO
    return True

async def run():
    try:
        websocket = await websockets.connect(os.getenv("xrpl_ws"))
        try:
            await pingpong(websocket)
            await do_subscribe(websocket)
            while True:
                message = await handler(websocket)
                transaction = json.loads(message)
                onTransactionReceived(transaction)
        except websockets.ConnectionClosed:
            print('Disconnected...')
        finally:
            await websocket.close()
    except websockets.WebSocketException as e:
        print("WebSocket connection failed:", e)
    except Exception as e:
        print("An error occurred:", e)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    print('WebSocket client finished.')

if __name__ == '__main__':
    main()
