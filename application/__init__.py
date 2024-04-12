from flask import Flask, request, redirect, url_for, render_template
import os
import pymysql
from web3 import Web3
from helpers.config import rpc_endpoints

eth_rpc_url = rpc_endpoints["ETH"]["url"]
celo_rpc_url = rpc_endpoints["CELO"]["url"]
web3 = Web3(Web3.HTTPProvider(eth_rpc_url))
Maticweb3 = Web3(Web3.HTTPProvider(celo_rpc_url))

application = Flask(__name__)

def get_db_connection():
    connection = pymysql.connect(host=os.getenv("HOST_NAME"),
                                 user=os.getenv("USER_NAME"),
                                 password=os.getenv("PASSWORD"),
                                 db=os.getenv("DBNAME"),
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection
