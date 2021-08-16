from get_client import client, OPERATOR_ID, OPERATOR_KEY, config_user_client
from create_account import HederaAccount, HederaData
from hedera import (
    Hbar,
    PrivateKey,
    AccountId,
    AccountCreateTransaction,
    TransferTransaction,
    TokenCreateTransaction,
    TokenAssociateTransaction,
    TokenGrantKycTransaction,
    TokenInfoQuery,
    )
from jnius import autoclass
import time

Collections = autoclass("java.util.Collections")

#1 First we create the tokens
#2 Then we associate accounts to the tokens
#3 Then we enable KYC (Know your customer)
#4 Transfer the token from tresurer to account then to another...

def create_token(**kwargs):

    decimals = kwargs.get("decimals")
    init_supply = kwargs.get("init_supply")
    token_name = kwargs.get("token_name")
    token_symbol = kwargs.get("token_symbol")
    node = kwargs.get("node")

    token_tran = TokenCreateTransaction(
    ).setNodeAccountIds(Collections.singletonList(node)
    ).setTokenName(token_name
    ).setTokenSymbol(token_symbol
    ).setDecimals(decimals
    ).setInitialSupply(init_supply
    ).setTreasuryAccountId(OPERATOR_ID
    ).setAdminKey(OPERATOR_KEY.getPublicKey()
    ).setFreezeKey(OPERATOR_KEY.getPublicKey()
    ).setWipeKey(OPERATOR_KEY.getPublicKey()
    ).setKycKey(OPERATOR_KEY.getPublicKey()
    ).setSupplyKey(OPERATOR_KEY.getPublicKey()
    ).setFreezeDefault(False
    ).execute(client)

    return token_tran.getReceipt(client).tokenId

class Tokens:

    def __init__(self, *args, **kwargs):

        self.token = kwargs.get("token")
        self.node = kwargs.get("node")

    def associate(self, **kwargs):
        self.acc = kwargs.get("acc")
        self.key = kwargs.get("key")
        token_ass = TokenAssociateTransaction(
        ).setNodeAccountIds(Collections.singletonList(self.node)
        ).setAccountId(AccountId.fromString(self.acc)
        ).setTokenIds(Collections.singletonList(self.token)
        ).freezeWith(client
        ).sign(OPERATOR_KEY
        ).sign(PrivateKey.fromString(self.key)
        ).execute(client)

        return token_ass

    def kyc(self, **kwargs):
        self.acc = kwargs.get("acc")
        kyc_tran = TokenGrantKycTransaction(
          ).setNodeAccountIds(Collections.singletonList(self.node)
          ).setAccountId(AccountId.fromString(self.acc)
          ).setTokenId(self.token
          ).execute(client
          ).getReceipt(client)

    def transfer(self, **kwargs):
        self.key =kwargs.get("key")
        self.acc_out = kwargs.get("acc_out")
        self.acc_in = kwargs.get("acc_in")
        self.amount = kwargs.get("amount")

        if self.key:
            transfer_tran = TransferTransaction(
              ).setNodeAccountIds(Collections.singletonList(self.node)
              ).addTokenTransfer(self.token, AccountId.fromString(self.acc_out), self.amount
              ).addTokenTransfer(self.token, AccountId.fromString(self.acc_in), abs(self.amount)
              ).freezeWith(client
              ).sign(PrivateKey.fromString(self.key)
              ).execute(client
              ).getReceipt(client)
        else:
            transfer_tran = TransferTransaction(
              ).setNodeAccountIds(Collections.singletonList(self.node)
              ).addTokenTransfer(self.token, AccountId.fromString(self.acc_out), self.amount
              ).addTokenTransfer(self.token, AccountId.fromString(self.acc_in), abs(self.amount)
              ).execute(client
              ).getReceipt(client)


class ManageTokens:

    def __init__(self, *args, **kwargs):

        self.init_supply = kwargs.get("init_supply")
        self.decimals = kwargs.get("decimals")
        self.token_name = kwargs.get("token_name")
        self.token_symbol = kwargs.get("token_symbol")

        new_acc_1 = HederaAccount().create_new_account()

        self.cust_acc_id_1 = new_acc_1["acc_id"]
        self.cust_public_key_1 = new_acc_1["public_key"]
        self.cust_private_key_1 = new_acc_1["private_key"]
        self.node = new_acc_1["node"]

        new_acc_2 = HederaAccount().create_new_account()

        self.cust_acc_id_2 = new_acc_2["acc_id"]
        self.cust_public_key_2 = new_acc_2["public_key"]
        self.cust_private_key_2 = new_acc_2["private_key"]

        self.client_1 = config_user_client(
            acc_id = self.cust_acc_id_1,
            private_key = self.cust_private_key_1
            )

        self.client_2 = config_user_client(
            acc_id = self.cust_acc_id_2,
            private_key = self.cust_private_key_2
            )

        self.token = create_token(
            init_supply = self.init_supply,
            decimals = self.decimals,
            token_name = self.token_name,
            token_symbol = self.token_symbol,
            node=self.node
            )

        self.token_tran = Tokens(node = self.node, token=self.token)

    def associate(self):
        ass = self.token_tran.associate(acc = self.cust_acc_id_1, key=self.cust_private_key_1)
        time.sleep(5)
        print(f"Associated account {self.cust_acc_id_1} with token {self.token.toString()}")

        ass = self.token_tran.associate(acc = self.cust_acc_id_2, key=self.cust_private_key_2)
        time.sleep(5)
        print(f"Associated account {self.cust_acc_id_2} with token {self.token.toString()}")


    def kyc(self, **kwargs):
        kyc = self.token_tran.kyc(acc = self.cust_acc_id_1)
        time.sleep(5)
        print(f"Granted KYC for account {self.cust_acc_id_1} on token {self.token.toString()}")

        kyc = self.token_tran.kyc(acc = self.cust_acc_id_2)
        time.sleep(5)
        print(f"Granted KYC for account {self.cust_acc_id_2} on token {self.token.toString()}")

    def transfer(self, **kwargs):
        #must be negative
        self.amount = kwargs.get("amount")
        
        tran = self.token_tran.transfer(
            acc_out = OPERATOR_ID.toString(),
            acc_in = self.cust_acc_id_1,
            amount=self.amount)

        time.sleep(5)
        print(f"Sent {abs(self.amount)} tokens from account {OPERATOR_ID.toString()} (Operator) to account {self.cust_acc_id_1}")

        tran = self.token_tran.transfer(
            acc_out = self.cust_acc_id_1,
            acc_in = self.cust_acc_id_2,
            key = self.cust_private_key_1,
            amount=self.amount)

        time.sleep(5)
        print(f"Sent {abs(self.amount)} tokens from account {self.cust_acc_id_1} to account {self.cust_acc_id_2}")

    def token_info(self):

        the_token = TokenInfoQuery(
            ).setTokenId(self.token
            ).execute(client)

        supply = the_token.totalSupply
        name = the_token.name
        symbol = the_token.symbol
        print(f'The token total supply is {supply}')
        print(f'The token name is "{name}"')
        print(f'The token symbol is "{symbol}"')


