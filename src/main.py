from crypto_main import *

def main():
    block: Block = Block()
    block.add_transaction(Transaction(1, 2, 100))
    block.add_transaction(Transaction(2, 3, 200))
    print(block.hash())
    print(block)

if __name__ == '__main__':
    main()
