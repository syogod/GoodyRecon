import requests
from urllib.parse import urlparse
import re
import os
import subprocess

def check_redirect_and_offer_hosts_entry(target, port):
    url = f"http://{target}:{port}"
    if port == 443:
        url = f"https://{target}"

    try:
        print(f"[*] Checking for 302 redirect on {url}...")
        response = requests.get(url, allow_redirects=False, timeout=5, verify=False)
        if response.status_code == 302:
            location = response.headers.get("Location", "")
            parsed = urlparse(location)

            if parsed.hostname and not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", parsed.hostname):
                print(f"[!] Detected redirect to: {parsed.hostname}")
                add = input(f"Add '{parsed.hostname} {target}' to /etc/hosts? [y/N]: ").lower()
                if add == 'y':
                    with open("/etc/hosts", "a") as f:
                        f.write(f"\n{target} {parsed.hostname}")
                    print("[+] Entry added to /etc/hosts.")
                else:
                    print("[*] Skipped /etc/hosts entry.")
                return parsed.hostname
        else:
            print(f"[*] No redirect found. Status: {response.status_code}")
    except Exception as e:
        print(f"[!] Error checking redirect: {e}")
    return None

def handle_http(target, port, queue, host_override):
    hostname = check_redirect_and_offer_hosts_entry(target, port)
    if hostname:
        host_override[port] = hostname
    used_host = host_override.get(port, target)

    print(f"[HTTP] Options for {used_host}:{port}")
    print("  1. Queue gobuster for directories")
    print("  2. Queue subdomain check")
    print("  3. Queue browser open")
    print("  4. Skip")
    choice = input("Select an option: ")

    url = f"http://{used_host}:{port}"
    if port == 443:
        url = f"https://{used_host}"

    if choice == "1":
        queue.append({
            "description": f"Gobuster scan on {url}",
            "function": lambda: subprocess.run([
                "gobuster", "dir", "-u", url, "-w", "/usr/share/wordlists/dirb/common.txt"
            ])
        })
    elif choice == "2":
        queue.append({
            "description": f"Subdomain check for {target}",
            "function": lambda: print("[!] Subdomain check not implemented yet.")
        })
    elif choice == "3":
        queue.append({
            "description": f"Open {url} in browser",
            "function": lambda: subprocess.run(["xdg-open", url])
        })
    else:
        print("[*] Skipping...")
