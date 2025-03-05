# Rail Bridge Server

description: |
  The Rail Bridge Server is an automated liqudity management system that enables fiat providers to listen for blockchain transactions and execute payouts 
  when payments are received. Providers run the Rail server to monitor blockchain 
  activity, and when a transaction reaches their address, they confirm it and process 
  a fiat payout.

  The system operates on multiple networks and supports various assets, making it a 
  robust decentralized financial infrastructure for automated cross-chain payouts.

supported_blockchains:
  - name: Stellar
    assets: ["USDC", "CNGN"]
    url: "https://stellar.org/"
  - name: Celo
    assets: ["CUSD"]
    url: "https://celo.org/"
  - name: Tron
    assets: ["USDT"]
    url: "https://tron.network/"
  - name: Binance Smart Chain (BSC)
    assets: ["CNGN"]
    url: "https://bscscan.com/"
  - name: Bantu Blockchain
    assets: ["CNGN"]
    url: "https://bantublockchain.org/"

demo_url: "https://liqudityrail.com"
api_docs: "https://docs.liqudityrail.com"

providers:
  registration: "https://liquidityrail.com/register"
  docker_image: "embonye/muda:latest"

docker_commands:
  pull: "docker pull embonye/muda:latest"
  run_provider: >
    docker run -d -p 8030:8000 --env-file /home/ec2-user/apps/config/rail.env 
    --name muda-container embonye/muda:latest provider service
  migrate_db: >
    docker run --env-file /home/ec2-user/apps/config/rail.env 
    embonye/muda:latest --migrate-db

configuration:
  general:
    DEBUG: true
    PORT: 8001
    address: "<BLOCKCHAIN_ADDRESS>"
    callback_url: "<CALLBACK_URL>"
    webhook_url: "<WEBHOOK_URL>"
    currency: "UGX"
    default_chain: "STELLAR, CELO, TRON, BSC, BANTU"

  database:
    HOST_NAME: "localhost"
    USER_NAME: "root"
    PASSWORD: "root"
    DBNAME: "liqudity_rail_server"

  provider_settings:
    mode: "dev"
    enc_key: "<ENCRYPTION_KEY>"
    RATE_ENDPOINT: "<RATE_EXCHANGE_URL>"
    PAYOUT_URL: "<PAYOUT_REQUEST_URL>"
    PROVIDER_NAME: "<PROVIDER_NAME>"
    PROVIDER_ID: "<PROVIDER_ID>"
    PAY_CURRENCY: "UGX"

  supported_assets: ["USDT", "USDC", "CNGN"]

clients:
  run_command: "python run.py provider client"
  responsibility: |
    Clients are responsible for entering their private keys for transactions. 
    The provider mode does not require private keys, as it only listens for incoming 
    transactions and processes payouts using configured endpoints.

api_reference: "https://docs.liqudityrail.com"
