import json
import typer
import os
import io
from contextlib import redirect_stdout

eco_mint = typer.Typer()

########################################################################################################################
## Class Transaction
########################################################################################################################
class Transaction:

    def __init__(self):
        with open("config.json", "r") as read_file:
            self.config = json.load(read_file)

        if not self.config.get("target_address"):
            raise TypeError("Not target address in config.json")
            return
        self.target_address = self.config["target_address"]

        if not self.config.get("multisig_address"):
            raise TypeError("Not multisig address in config.json")
            return
        self.multisig_address = self.config["multisig_address"]

        if not self.config.get("source_address"):
            raise TypeError("Not source address in config.json")
            return
        self.source_address = self.config["source_address"]

        if not self.config.get("target_function"):
            raise TypeError("Missing tag target_function in config.json")
            return

        if not self.config.get("endpoint"):
            raise TypeError("Not endpoint in config.json")
            return
        self.endpoint = self.config["endpoint"]

        self.entrypoint = ""
        self.michelson_target_type_value = ""
        self.secret_key = ""
        self.signatures = ""
        self.transaction_bytes = ""
        self.transfer_amount = 0
        self.transfer_address = ""
        self.transfer_destination = ""
        self.lambda_param = ""

    def create_fund_lambda(self):
        my_lambda = '{ { DROP ;    NIL operation ;    PUSH address "%s" ;    CONTRACT unit ;    IF_NONE { PUSH int 7 ; FAILWITH } {} ;    PUSH mutez %d ;    UNIT ;    TRANSFER_TOKENS ;    CONS } }' \
                    % (self.transfer_address,
                       self.transfer_amount)
        transaction = "tezos-client --endpoint %s normalize data '%s' of type 'lambda unit (list operation)' --unparsing-mode Optimized" % (self.endpoint, my_lambda)
        return transaction

    def create_lambda(self):
        my_lambda = '{ { DROP ;    NIL operation ;    PUSH address "%s" ;    CONTRACT %%%s %s ;    IF_NONE { PUSH int 16 ; FAILWITH } {} ;    PUSH mutez %d ;    PUSH %s %s ;    TRANSFER_TOKENS ;    CONS } }' \
                    % (self.target_address,
                       self.entrypoint,
                       self.config["target_function"][self.entrypoint]["michelson_type"], 0,
                       self.config["target_function"][self.entrypoint]["michelson_type"],
                       self.michelson_target_type_value)
        transaction = "tezos-client --endpoint %s normalize data '%s' of type 'lambda unit (list operation)' --unparsing-mode Optimized" % (self.endpoint, my_lambda)
        return transaction

    def lambda_bytes(self):
        transaction = "tezos-client --endpoint %s prepare multisig transaction on %s running lambda '%s' --bytes-only" \
                      % (self.endpoint, self.multisig_address, self.lambda_param)
        return transaction

    def sign(self):
        transaction = "tezos-client --endpoint %s sign bytes '%s' for %s" % \
                      (self.endpoint, self.transaction_bytes, self.secret_key)
        return transaction

    def run(self):
        transaction = "tezos-client --endpoint %s run transaction %s on multisig contract %s on behalf of %s with signatures %s" % \
                      (self.endpoint, self.transaction_bytes, self.multisig_address, self.source_address, self.signatures)
        return transaction

    def transfer_bytes(self):
        transaction = "tezos-client --endpoint %s prepare multisig transaction on %s transferring %d to %s --bytes-only" % \
                      (self.endpoint, self.multisig_address, self.transfer_amount, self.transfer_destination)
        return transaction

    def decode(self):
        transaction = "tezos-client --endpoint %s unpack michelson data %s" % (self.endpoint, self.transaction_bytes)
        return transaction

########################################################################################################################
## CLI commands
########################################################################################################################
@eco_mint.command()
def lamb(entrypoint :str, val :str):
    '''
    Generate lambda
    '''
    transaction = Transaction()
    transaction.entrypoint = entrypoint
    transaction.michelson_target_type_value = val
    command = transaction.create_lambda()
    #f = io.StringIO()
    #with redirect_stdout(f):
    os.system(command)
    #print('Got stdout: "{0}"'.format(f.getvalue()))

@eco_mint.command()
def fund(amount :int, dst :str):
    '''
    Generate lambda for fund transfer
    '''
    transaction = Transaction()
    transaction.transfer_address = dst
    transaction.transfer_amount = amount
    command = transaction.create_fund_lambda()
    os.system(command)

@eco_mint.command()
def decode(transaction_bytes :str):
    '''
    Decode transaction bytes
    '''
    transaction = Transaction()
    transaction.transaction_bytes = transaction_bytes
    command = transaction.decode()
    print("\n--> Transaction command:")
    print(command)
    print("\n--> Execute command:")
    os.system(command)

@eco_mint.command()
def transfer_bytes(amount :int, dst :str):
    '''
    Get transaction bytes to sign for transfer operation
    '''
    if amount <= 0:
        raise TypeError("Invalid amount")
        return
    transaction = Transaction()
    transaction.transfer_amount = amount
    transaction.transfer_destination = dst
    command = transaction.transfer_bytes()
    print("\n--> Transaction command:")
    print(command)
    print("\n--> Execute command:")
    os.system(command)

@eco_mint.command()
def lambda_bytes(lamb :str):
    '''
    Get transaction bytes to sign for lambda operation
    '''
    transaction = Transaction()
    transaction.lambda_param = lamb
    command = transaction.lambda_bytes()
    print("\n--> Transaction command:")
    print(command)
    print("\n--> Execute command:")
    val = os.system(command)

@eco_mint.command()
def sign(transaction_bytes :str, secret_key :str):
    '''
    Get transaction and sign it with the secret key
    '''
    transaction = Transaction()
    transaction.transaction_bytes = transaction_bytes
    transaction.secret_key = secret_key
    command = transaction.sign()
    print("\n--> Transaction command:")
    print(command)
    print("\n--> Execute command:")
    os.system(command)

@eco_mint.command()
def run(transaction_bytes :str, signatures :str):
    '''
    Run transaction in multisig contract
    '''
    transaction = Transaction()
    transaction.signatures = signatures
    transaction.transaction_bytes = transaction_bytes
    command = transaction.run()
    print("\n--> Transaction command:")
    print(command)
    print("\n--> Execute command:")
    os.system(command)

########################################################################################################################
## Main
########################################################################################################################
if __name__ == '__main__':
    eco_mint()
