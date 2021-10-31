import base64
import hashlib
import json
import os
from time import sleep
from datetime import date
from os.path import dirname
import pandas as pd
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from web3 import Web3
from werkzeug.security import generate_password_hash

load_dotenv()

CONTRACT_CSV_FILEPATH = dirname(__file__) + '/contracts.csv'
FILEPATH = dirname(__file__) + '/accounts.csv'
IPC_FILE = '/home/trikiomar/nodes/node1/geth.ipc'
W3 = Web3(Web3.IPCProvider(IPC_FILE))
COINTBASE = W3.eth.coinbase
ABI = json.loads(open('./contract-abi.txt').read().replace('\n', '').replace('\t', ''))
BYTECODE = open('./contract-bin.txt', 'r').read().replace('\n', '')
FERNET = Fernet(
    base64.b64encode(hashlib.pbkdf2_hmac('sha256', os.environ.get('FERNET_KEY').encode('ascii'),
                                         'hEq52fRbu1WGrU2TIsZ3vtFf7xJp2SMOEC4'.encode('ascii'),
                                         1000))
)


def submit_transaction_hash(transaction_hash):
    W3.geth.miner.start(1)
    while True:
        try:
            tx_receipt = W3.eth.wait_for_transaction_receipt(transaction_hash)
            sleep(10)
            if tx_receipt is not None:
                W3.geth.miner.stop()
                return tx_receipt
        except Exception as exception:
            print(exception, end="")


def deploy_contract():
    contract = W3.eth.contract(abi=ABI, bytecode=BYTECODE).constructor()
    gas_price = contract.estimateGas()
    authenticated = W3.geth.personal.unlock_account(COINTBASE, '11608168')
    if authenticated:
        tx = contract.transact({
            'from': W3.eth.coinbase,
            'nonce': W3.eth.get_transaction_count(COINTBASE),
            'gasPrice': gas_price
        })
        W3.geth.miner.start(1)
        tx_receipt = submit_transaction_hash(tx)
        if tx_receipt is not None and tx_receipt.contractAddress is not None:
            dataframe = pd.read_csv(CONTRACT_CSV_FILEPATH, sep=";")
            dataframe = dataframe.append(
                {
                    'contractAddress': tx_receipt.contractAddress,
                    'dateDeployment': date.today()
                },
                ignore_index=True
            )
            dataframe.to_csv(CONTRACT_CSV_FILEPATH, sep=";", index=False)
            return tx_receipt.contractAddress
    else:
        return Exception("not authenticated")


def submit_secure_transaction(function, passphrase, private_key_encrypted, to=None, data=None):
    try:
        account = W3.eth.account.privateKeyToAccount(
            hex(int(FERNET.decrypt(private_key_encrypted.encode('utf-8')), 16))
        )
        transaction = {
            'from': account.address,
            'nonce': W3.eth.get_transaction_count(account.address),
        }
        if to is not None:
            transaction['to'] = to
        if data is not None:
            transaction['data'] = data

        if W3.geth.personal.unlock_account(account.address, passphrase):
            signed_tansaction = W3.eth.account.sign_transaction(
                function.buildTransaction(transaction=transaction),
                private_key=account.privateKey
            )
            return submit_transaction_hash(W3.eth.send_raw_transaction(signed_tansaction.rawTransaction))
        return Exception("can't authenticate")
    except Exception as exception:
        return exception


class UserAuthenticationService(object):
    accounts = pd.read_csv(FILEPATH, sep=";")

    def create_account(self, passphrase):
        try:
            account = W3.geth.personal.new_account(passphrase)
            self.add_ethers(account)
            private_key = W3.eth.account.decrypt(
                open(W3.geth.personal.list_wallets()[-1].url.replace('keystore://', '')).read(),
                passphrase
            ).hex()
            encrypted = FERNET.encrypt(private_key.encode('utf-8'))
            self.accounts = self.accounts.append(
                {'account': account, 'privateKey': encrypted}, ignore_index=True)
            self.accounts.to_csv(FILEPATH, sep=";", index=False)
            return {
                'address': account,
                'privateKey': encrypted,
                'passwordRecuperationCode': generate_password_hash(private_key)
            }
        except Exception as exception:
            return exception

    @staticmethod
    def add_ethers(address, ethers=100000000000000):
        W3.geth.miner.set_etherbase(address)
        W3.geth.miner.start(1)
        while True:
            sleep(10)
            balence = W3.eth.get_balance(address)
            if balence >= ethers:
                W3.geth.miner.stop()
                if address != COINTBASE:
                    W3.geth.miner.set_etherbase(COINTBASE)
                return address

    def login(self, address, passphrase):
        try:
            account = W3.toChecksumAddress(address)
            private_key_encrypted = self.accounts.loc[self.accounts['account'] == address]['privateKey'].values[0]
            if private_key_encrypted:
                private_key = hex(int(FERNET.decrypt(private_key_encrypted.encode('utf-8')), 16))
                account = W3.eth.account.privateKeyToAccount(private_key)
                if account and W3.geth.personal.unlock_account(account.address, passphrase):
                    return {
                        'address': account.address,
                        'privateKey': private_key_encrypted
                    }
            return W3.geth.personal.unlock_account(account.address, passphrase)
        except Exception as exception:
            return exception


class PatientPrivateDataService(object):

    def __init__(self, contract_address):
        self.contract = W3.eth.contract(address=contract_address, abi=ABI)
        self.accounts = pd.read_csv(FILEPATH, sep=";")

    def get_patient_by_id(self, _id: int):
        data = self.contract.functions.getPatientById(_id).call()
        return {
            'id': data[0],
            'name': data[1],
            'familyName': data[2],
            'birthdate': data[3],
            'school': data[4],
            'parent_id': data[5]
        }

    def create_or_update_patient(self, _id: int, name: str, family_name: str, birthdate: str, school, parent_id,
                                 address, passphrase, is_new=True) -> Exception or dict:
        try:
            private_key_encrypted = self.accounts.loc[self.accounts['account'] == address]['privateKey'].values[0]
            if is_new:
                function = self.contract.functions.createPatient(_id, name, family_name, birthdate, school,
                                                                 parent_id)
            else:
                function = self.contract.functions.updatePatient(_id, name, family_name, birthdate, school)
            tx_receipt = submit_secure_transaction(function=function, private_key_encrypted=private_key_encrypted,
                                                   passphrase=passphrase)
            if tx_receipt is not None and not isinstance(tx_receipt, Exception):
                return {
                    'id': _id,
                    'name': name,
                    'familyName': family_name,
                    'birthdate': birthdate,
                    'school': school,
                    'parentId': parent_id
                }
            return tx_receipt
        except Exception as exception:
            return exception

    def delete_patient(self, _id: int, address: str, passphrase: str):
        try:
            private_key_encrypted = self.accounts.loc[self.accounts['account'] == address]['privateKey'].values[0]
            patient = self.get_patient_by_id(_id)
            if patient.get('id') == 0:
                return False
            deleted = submit_secure_transaction(function=self.contract.functions.deletePatient(patient.get('id')),
                                                passphrase=passphrase, private_key_encrypted=private_key_encrypted)
            if isinstance(deleted, Exception):
                return deleted
            return True
        except Exception as exception:
            return exception
