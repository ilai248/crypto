import sys, time, threading
from blockchain__impl import BlockchainUser
from security import get_public_key_str
from colorama import init, Fore, Style

# Initialize colorama for colorful terminal output
init(autoreset=True)


def start_node(node_id):
    port = 5000 + int(node_id)
    user = BlockchainUser(port, node_id)
    time.sleep(2)  # Wait briefly for peer discovery

    # Start CLI in a separate thread
    cli_thread = threading.Thread(target=process_commands, args=(user,), daemon=True)
    cli_thread.start()

    # Keep running
    while True:
        while not user.can_create():
            time.sleep(0.1)
        print("Trying to create block.")
        interval = user.curr_interval()
        user.create_blockrequest(user.interval_time(interval), user.interval_time(interval + 1))
        time.sleep(user.interval_time(interval + 1) - time.time())  # Wait until next interval


def process_commands(user):
    """Process terminal commands in a separate thread."""
    print(f"{Fore.CYAN}Welcome to the Blockchain CLI! Type 'help' for commands.{Style.RESET_ALL}")
    while True:
        try:
            command = input(f"{Fore.CYAN}>>> {Style.RESET_ALL}").strip().lower()
            args = command.split()
            if not args:
                continue

            cmd = args[0]
            if cmd == "help":
                print(f"{Fore.YELLOW}Available commands:")
                print(f"  send <public_key> <amount> - Send <amount> to <public_key> (hex)")
                print(f"  key - Print your public key")
                print(f"  help - Show this help message")
                print(f"  exit - Stop the node")
                print(Style.RESET_ALL)
            elif cmd == "key":
                print(f"{Fore.YELLOW}Public Key:")
                print(get_public_key_str())
                print(Style.RESET_ALL)
            elif cmd == "send":
                if len(args) != 3:
                    print(f"{Fore.RED}Usage: send <public_key> <amount>{Style.RESET_ALL}")
                    continue
                try:
                    receiver_key = args[1]
                    amount = float(args[2])
                    # Validate inputs
                    if amount <= 0:
                        print(f"{Fore.RED}Amount must be positive{Style.RESET_ALL}")
                        continue

                    # Check if user was added
                    if not user.valid:
                        print(f"{Fore.RED}Cannot send transaction: user hasn't yet been added to blockchain{Style.RESET_ALL}")
                        continue

                    # Check if money_heap is initialized
                    if user.money_heap is None:
                        print(f"{Fore.RED}Cannot send transaction: money_heap not initialized{Style.RESET_ALL}")
                        continue

                    # Get sender's balance info
                    sender_balance = user.get_balance_info()
                    if sender_balance.money < amount:
                        print(f"{Fore.RED}Insufficient balance: {sender_balance.money} available{Style.RESET_ALL}")
                        continue

                    # Create and broadcast transaction
                    user.gossip.broadcast_verifyTransactionRequest(
                        sender=sender_balance.public_key,
                        sender_balance=sender_balance,
                        receiver=receiver_key,
                        amount=amount
                    )
                    print(f"{Fore.GREEN}Transaction sent: {amount} to {receiver_key}{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}Invalid amount: must be a number{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}Error sending transaction: {e}{Style.RESET_ALL}")

            elif cmd == "exit":
                print(f"{Fore.YELLOW}Shutting down node...{Style.RESET_ALL}")
                user.gossip.stop()
                sys.exit(0)

            else:
                print(f"{Fore.RED}Unknown command: {cmd}. Type 'help' for commands.{Style.RESET_ALL}")

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Use 'exit' to stop the node gracefully{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error processing command: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"{Fore.RED}Usage: python main.py <node_id>{Style.RESET_ALL}")
        sys.exit(1)
    start_node(sys.argv[1])
