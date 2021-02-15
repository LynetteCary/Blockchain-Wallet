import subprocess
import json
import os
from constants import *
from pathlib import Path
from dotenv import load_dotenv
from bit import *
from bit.network import NetworkAPI
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from getpass import getpass

env_path = Path('.', '.env')
load_dotenv(dotenv_path=env_path)

mnemonic = os.getenv('MNEMONIC')
#print(mnemonic)


# derive the wallet keys
def derive_wallets(mnemonic, coin, numderive):
    command = f'php ./hd-wallet-derive/hd-wallet-derive.php -g --mnemonic="{mnemonic}" --coin="{coin}" --numderive="{numderive}" --cols=address,index,path,privkey,pubkey,pubkeyhash,xprv,xpub --format=json'

    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    #print(output)

    keys = json.loads(output)
    return keys

numderive = 3
coin = {"btc-test": derive_wallets(mnemonic, BTCTEST, numderive), "eth": derive_wallets(mnemonic, ETH, numderive)}
print(json.dumps(coin, indent=2, sort_keys=True))

btctest_privkey = coin[BTCTEST][0]['privkey']
eth_privkey = coin[ETH][0]['privkey']
print(json.dumps(btctest_privkey))
print(json.dumps(eth_privkey))

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# convert privkey string to transact
def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    elif coin == BTCTEST:
        return PrivateKeyTestnet(priv_key)


# create unsigned transaction
def create_tx(coin, account, to, amount):
    if coin == ETH:
        gasEstimate = w3.eth.estimateGas({"to": to, "from": account.address, "value": amount}) 
        return {"to": to, "from": account.address, "value": amount, "gas": gasEstimate, "gasPrice": w3.eth.gasPrice, "nonce": w3.eth.getTransactionCount(account.address), "chainID": w3.eth.net.geldId()}
    elif coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])


# sign and send the transaction
def send_tx(coin, account, to, amount):
        if coin == ETH:
            raw_tx = create_tx(coin, account, to, amount)
            signed_tx = account.sign_transaction(raw_tx)
            result = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            print(result.hex())
            return result.hex()
        
        elif coin == BTCTEST:
            raw_tx = create_tx(coin, account, to, amount)
            signed_tx = account.sign_transaction(raw_tx)
            return NetworkAPI.broadcast_tx_testnet(signed_tx)


# Send BTCTEST transaction
btc_key = coin[BTCTEST][0]['privkey']
btc_address = coin[BTCTEST][1]['address']
send_tx(BTCTEST, priv_key_to_account(BTCTEST, btc_key),btc_address, 0.00001)

# Send ETH transaction
eth_key = coin[ETH][0]['privkey']
eth_address = coin[ETH][1]['address']
send_tx(ETH, priv_key_to_account(ETH, eth_key),eth_address, 0.00001)