from colorama import Fore, Style, init
import socket

init(autoreset=True)

def print_green(msg):
    print(Fore.GREEN + msg + Style.RESET_ALL)

def print_yellow(msg):
    print(Fore.YELLOW + msg + Style.RESET_ALL)

def print_red(msg):
    print(Fore.RED + msg + Style.RESET_ALL)

def print_cyan(msg):
    print(Fore.CYAN + msg + Style.RESET_ALL)

def prompt_input(message, default, color=Fore.CYAN):
    return input(color + message + Style.RESET_ALL) or default

def valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except: 
        return False
