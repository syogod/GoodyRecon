import subprocess
import re
from utils import print_green, print_yellow, print_red, prompt_input

def run_nmap_scan(target):
    # Run an Nmap scan with service/version detection and no ping
    print_green(f"[+] Running Nmap scan on {target}...")
    result = subprocess.run(["nmap", "-sV", "-Pn", target], capture_output=True, text=True)
    return result.stdout

def parse_nmap_output(nmap_output):
    # Parse Nmap output to extract open TCP ports and their services
    open_ports = []
    for line in nmap_output.splitlines():
        match = re.match(r"(\d+)/tcp\s+open\s+(\S+)", line)
        if match:
            port, service = match.groups()
            open_ports.append((int(port), service))
    return open_ports
