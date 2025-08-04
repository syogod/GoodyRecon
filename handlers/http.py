import requests
from urllib.parse import urlparse
import re
import os
import subprocess
import hashlib
import threading
import time
import sys

def spinner(stop_event):
    animation = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r[*] Gobuster running... {animation[idx % len(animation)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write("\r[*] Gobuster finished.               \n")

def get_soft_404_fingerprint(url):
    try:
        r = requests.get(url, timeout=5, verify=False)
        return {
            "status": r.status_code,
            "length": len(r.content),
            "hash": hashlib.sha1(r.content).hexdigest(),
            "snippet": r.text[:200].strip()
        }
    except Exception as e:
        print(f"[!] Error fingerprinting soft 404: {e}")
        return None
    
def analyze_soft_404(url):
    print(f"[*] Checking for soft 404 behavior at {url}")
    fingerprint = get_soft_404_fingerprint(url + "/nonexistent-xyz123")
    if fingerprint:
        print(f"    Status: {fingerprint['status']}")
        print(f"    Length: {fingerprint['length']}")
        print(f"    SHA1  : {fingerprint['hash']}")
        print("    Snippet:")
        print("    " + fingerprint['snippet'].replace('\n', '\n    '))

        exclude = input("Use --exclude-length for this? [y/N]: ").lower()
        if exclude == 'y':
            return fingerprint['length']
    return None

def gobuster_scan(url, exclude_length=None, follow_redirects=False):
    args = [
        "gobuster", "dir", "-u", url,
        "-w", "/usr/share/wordlists/dirb/common.txt"
    ]
    if follow_redirects:
        args.append("-r")
    if exclude_length:
        args += ["--exclude-length", str(exclude_length)]

    print(f"[~] Running Gobuster on {url}...")

    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner, args=(stop_event,))
    spinner_thread.start()

    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        # Print each line as Gobuster outputs it
        for line in process.stdout:
            if line.strip():
                print("\r" + " " * 60 + "\r", end="")  # Clear spinner line
                print(line.strip())
        process.wait()
    finally:
        stop_event.set()
        spinner_thread.join()

    stderr = process.stderr.read()

    if ("Error: the server returns a status code that matches the provided options" in stderr and
        "=> 302" in stderr):
        if not follow_redirects:
            print("[!] Gobuster failed due to 302 redirects.")
            print("[~] Retrying with -r (follow redirects)...")
            return gobuster_scan(url, exclude_length=exclude_length, follow_redirects=True)
        else:
            print("[!] Gobuster still failed even with -r:")
            print(stderr)
    elif "Error: the server returns a status code that matches the provided options" in stderr:
        print("[!] Gobuster encountered soft 404 behavior (non-302).")
        print(stderr)


def get_protocol_and_url(target, port, service):
    # crude but effective
    service = service.lower()
    if "https" in service or "ssl" in service:
        protocol = "https"
    else:
        protocol = "http"
    url = f"{protocol}://{target}:{port}"
    return protocol, url

def is_hostname_in_hosts(hostname):
    try:
        with open("/etc/hosts", "r") as f:
            return any(hostname in line for line in f if not line.strip().startswith("#"))
    except Exception as e:
        print(f"[!] Failed to read /etc/hosts: {e}")
        return False
    
def check_redirect_and_offer_hosts_entry(url, ip):
    try:
        print(f"[~] Checking for redirects on {url}")
        response = requests.get(url, timeout=5, allow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get("Location", "")
            if location.startswith("http"):
                redirected_host = location.split("//")[1].split("/")[0]
                if redirected_host != ip:
                    print(f"[!] Detected 302 redirect from IP to hostname: {redirected_host}")
                    if is_hostname_in_hosts(redirected_host):
                        print(f"[~] Hostname {redirected_host} already in /etc/hosts. Skipping.")
                    else:
                        choice = input(f"[?] Add {ip} {redirected_host} to /etc/hosts? (y/n): ").lower()
                        if choice == "y":
                            try:
                                with open("/etc/hosts", "a") as f:
                                    f.write(f"{ip} {redirected_host}\n")
                                print("[+] Added to /etc/hosts.")
                                return redirected_host
                            except PermissionError:
                                print("[!] Permission denied. Try running with sudo.")
                        else:
                            print("[~] Skipping hosts file update.")
                    return redirected_host
    except Exception as e:
        print(f"[!] Redirect check failed: {e}")
    return None

def handle_http(target, port, queue, host_override, service="http"):
    protocol, base_url = get_protocol_and_url(target, port, service)

    hostname = check_redirect_and_offer_hosts_entry(base_url, target)
    if hostname:
        host_override[port] = hostname
    used_host = host_override.get(port, target)

    url = f"{protocol}://{used_host}:{port}"

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
        exclude_length = analyze_soft_404(url)

        queue.append({
        "description": f"Gobuster scan on {url}",
        "function": lambda: gobuster_scan(url, exclude_length=exclude_length)
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
