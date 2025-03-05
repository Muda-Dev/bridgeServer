# Rail Bridge Server

  The Rail Bridge Server is a a system that allows liqudity rail providers to listen for blockchain transactions and execute payouts when payments are received. Providers run the Rail server to monitor blockchain activity, and when a transaction reaches their address, they confirm it and process a fiat payout.

  The system operates on multiple networks and supports various assets, making it a robust decentralized financial infrastructure for automated cross-chain payouts.

  ## Supported Blockchains & Assets
  The system operates on the following blockchain networks:

  1. [Stellar](https://stellar.org/) - USDC, CNGN
  2. [Celo](https://celo.org/) - CUSD
  3. [Tron](https://tron.network/) - USDT
  4. [Binance Smart Chain (BSC)](https://bscscan.com/) - CNGN
  5. [Bantu Blockchain](https://bantublockchain.org/) - CNGN

  You can configure the default blockchain in the `.env` file or set it to `0` to support all chains.

  ## Demo
  You can see a working demo at:
  [Liquidity Rail Demo](https://liqudityrail.com)

  ## API Documentation
  For full API details, please check:
  [Liquidity Rail API Docs](https://docs.liqudityrail.com)

  # Providers

  ## Becoming a Provider
  Before running the server as a provider, you need to create an account at:

  [Liquidity Rail Registration](https://liquidityrail.com/register)

  During registration, choose the option to become a provider.

  ## Downloading and Running the Server

  The Rail Bridge Server is available as a Docker image for easy deployment.

  ### Pulling the Docker Image
  To use the Rail Bridge Server as a provider, you need to pull the Docker image:
  ```sh
   docker pull embonye/muda:latest
  ```

  ### Running the Server
  To run the server as a provider, use the following command:
  ```sh
  docker run -d -p 8030:8000 --env-file /home/ec2-user/apps/config/rail.env --name muda-container embonye/muda:latest
  ```

  ### Running Database Migrations
  Before starting the server, migrate the database using:
  ```sh
  docker run --env-file /home/ec2-user/apps/config/rail.env embonye/muda:latest --migrate-db
  ```

  ### Running the Server as a Service Provider
  ```sh
  docker run -d -p 8030:8000 --env-file /home/ec2-user/apps/config/rail.env --name muda-container embonye/muda:latest provider service
  ```

  The server will start a blockchain listening service, which listens for events emitted by the contract. Once a new payment is received, a callback will be sent to the `callback_url`.

  ## Configuration
  The `.env` file must be present in the working directory and should contain the following values:

  ### General Settings
  - `DEBUG=True`
  - `PORT=8001`
  - `address` - The blockchain address that will be receiving payments.
  - `callback_url` - URL that will be called when a new payment has been received.
  - `webhook_url` - URL that will receive payment notifications once a transaction is completed.
  - `currency` - The default currency for payouts (e.g., UGX, USD, EUR, etc.).
  - `default_chain` - The blockchain used for transactions (CELO, STELLAR, TRON, BSC, BANTU, etc.).

  ### Database Configuration
  - `database`
    - `HOST_NAME=localhost`
    - `USER_NAME=root`
    - `PASSWORD=root`
    - `DBNAME=liqudity_rail_server`

  ### Provider-Specific Settings
  - `mode=dev`
  - `enc_key` - Encryption key used to sign callbacks.
  - `RATE_ENDPOINT` - Exchange rate endpoint for providers.
  - `PAYOUT_URL` - URL where fiat payouts are requested.
  - `PROVIDER_NAME` - Name of the provider.
  - `PROVIDER_ID` - Unique identifier for the provider.
  - `PAY_CURRENCY` - The currency for payouts.

  ### Supported Assets
  - `SUPPORTED_ASSETS=["USDT", "USDC", "CNGN"]`

  # Clients
  Clients use this service by running:
  ```sh
  python run.py provider client
  ```
  Clients are responsible for entering their private keys for transactions. The provider mode does not require private keys, as it only listens for incoming transactions and processes payouts using configured endpoints.

  Full API documentation is available:
  [here](https://docs.liqudityrail.com)
