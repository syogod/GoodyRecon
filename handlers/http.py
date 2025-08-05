import requests
from urllib.parse import urlparse
import re
import os
import subprocess
import threading
import time
import sys
from utils import print_green, print_yellow, print_red, prompt_input, valid_ip

def spinner(stop_event):
    # Spinner animation for long-running tasks (e.g., Gobuster)
    animation = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r[*] Gobuster running... {animation[idx % len(animation)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    print_green("\r[*] Gobuster finished.               \n")

def get_soft_404_fingerprint(url):
    # Attempt to fingerprint a soft 404 by requesting a non-existent page
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 404:
            print_green("[*] No soft 404 detected")
            return None
        else:
            # Return fingerprint details if not a hard 404
            return {
                "status": r.status_code,
                "length": len(r.content),
                "snippet": r.text[:200].strip()
            }
    except Exception as e:
        print_red(f"[!] Error fingerprinting soft 404: {e}")
        return None
    
def analyze_soft_404(url):
    # Analyze if the target exhibits soft 404 behavior
    print_green(f"[*] Checking for soft 404 behavior at {url}")
    fingerprint = get_soft_404_fingerprint(url + "/nonexistent-xyz123")
    if fingerprint:
        print_yellow("[!] Potential soft 404 behavior detected")
        print_yellow(f"    Status: {fingerprint['status']}")
        print_yellow(f"    Length: {fingerprint['length']}")
        print_yellow("    Snippet:")
        print_yellow("    " + fingerprint['snippet'].replace('\n', '\n    '))

        exclude = prompt_input("Use --exclude-length for this? [Y/n]: ","Y").lower()
        if exclude == 'y':
            return fingerprint['length']
    return None

def gobuster_scan(url, exclude_length=None, ignore_redirects=False):
    # Only analyze soft 404 if exclude_length is not provided
    if exclude_length is None:
        exclude_length = analyze_soft_404(url)
    # Run Gobuster directory brute-force scan with optional exclude-length and redirect ignore
    args = [
        "gobuster", "dir", "-u", url,
        "-w", "/usr/share/wordlists/dirb/common.txt"
    ]
    if ignore_redirects:
        args += ["-b", "302,404"]
    if exclude_length:
        args += ["--exclude-length", str(exclude_length)]

    print_green(f"[~] Running Gobuster on {url}...")

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

    # Handle Gobuster errors related to redirects or soft 404s
    if ("Error: the server returns a status code that matches the provided options" in stderr and
        "=> 302" in stderr):
        if not ignore_redirects:
            print_yellow("[!] Gobuster failed due to 302 redirects.")
            print_yellow("[~] Retrying with -b (ignore redirects)...")
            return gobuster_scan(url, exclude_length=exclude_length, ignore_redirects=True)
        else:
            print_red("[!] Gobuster still failed even with -r:")
            print(stderr)
    elif "Error: the server returns a status code that matches the provided options" in stderr:
        print_yellow("[!] Gobuster encountered soft 404 behavior (non-302).")
        print(stderr)

def get_protocol_and_url(target, port, service):
    # Determine protocol (http/https) based on service name
    service = service.lower()
    if "https" in service or "ssl" in service:
        protocol = "https"
    else:
        protocol = "http"
    url = f"{protocol}://{target}:{port}"
    return protocol, url

def is_hostname_in_hosts(hostname):
    # Check if a hostname is already present in /etc/hosts
    try:
        with open("/etc/hosts", "r") as f:
            return any(hostname in line for line in f if not line.strip().startswith("#"))
    except Exception as e:
        print_red(f"[!] Failed to read /etc/hosts: {e}")
        return False
    
def check_redirect_and_offer_hosts_entry(url, ip):
    # Check for 302 redirect and offer to add hostname to /etc/hosts if needed
    try:
        print_green(f"[~] Checking for redirects on {url}")
        response = requests.get(url, timeout=5, allow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get("Location", "")
            if location.startswith("http"):
                redirected_host = urlparse(location).hostname
                if redirected_host != ip:
                    print_yellow(f"[!] Detected 302 redirect from {ip} to hostname: {redirected_host}")
                    if is_hostname_in_hosts(redirected_host):
                        print_green(f"[~] Hostname {redirected_host} already in /etc/hosts. Skipping.")
                    else:
                        choice = prompt_input(f"[?] Add {ip} {redirected_host} to /etc/hosts? (Y/n): ", "Y").lower()
                        if choice == "y":
                            try:
                                with open("/etc/hosts", "a") as f:
                                    f.write(f"{ip} {redirected_host}\n")
                                print_green("[+] Added to /etc/hosts.")
                                return redirected_host
                            except PermissionError:
                                print_red("[!] Permission denied. Try running with sudo.")
                        else:
                            print_green("[~] Skipping hosts file update.")
                    return redirected_host
    except Exception as e:
        print_red(f"[!] Redirect check failed: {e}")
    return None

def gobuster_dns(domain):
    # Run Gobuster DNS mode for subdomain enumeration
    wordlist = "/usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-20000.txt"
    args = [
        "gobuster", "dns", "-q", "-z", "-d", domain,
        "-w", wordlist
    ]
    print_green(f"[~] Running Gobuster DNS on {domain}...")

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
        for line in process.stdout:
            if line.strip():
                print("\r" + " " * 60 + "\r", end="")  # Clear spinner line
                print(line.strip())
        process.wait()
    finally:
        stop_event.set()
        spinner_thread.join()

    stderr = process.stderr.read()
    if stderr:
        print_red(stderr)

def gobuster_vhost(domain):
    # Run Gobuster vhost mode for virtual host enumeration
    wordlist = "/usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-20000.txt"
    args = [
        "gobuster", "vhost", "-q", "-z", "-u", f"http://{domain}",
        "-w", wordlist
    ]
    print_green(f"[~] Running Gobuster VHOST on {domain}...")

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
        for line in process.stdout:
            if line.strip():
                print("\r" + " " * 60 + "\r", end="")  # Clear spinner line
                print(line.strip())
        process.wait()
    finally:
        stop_event.set()
        spinner_thread.join()

    stderr = process.stderr.read()
    if stderr:
        print_red(stderr)

def handle_http(target, port, queue, host_override, service="http"):
    # Main handler for HTTP/HTTPS services
    protocol, base_url = get_protocol_and_url(target, port, service)

    # If target is an IP, check for redirects and offer to update /etc/hosts
    if(valid_ip(target)):
        hostname = check_redirect_and_offer_hosts_entry(base_url, target)
        if hostname:
            host_override[port] = hostname
            target = host_override.get(port, target)

    url = f"{protocol}://{target}:{port}"

    # Define action keys and descriptions
    actions = [
        {"key": "1", "desc": "Queue gobuster for directories"},
        {"key": "2", "desc": "Queue subdomain check"},
        {"key": "3", "desc": "Queue vhost scan"},
        {"key": "4", "desc": "Queue browser open"},
        {"key": "5", "desc": "Done (finish selecting actions for this port)"}
    ]
    # Map action keys to unique queue descriptions for this port
    action_descriptions = {
        "1": f"Gobuster scan on {url}",
        "2": f"Subdomain check for {target}",
        "3": f"Vhost scan for {target}",
        "4": f"Open {url} in browser"
    }

    # Track which actions have been queued for this port
    queued_keys = set()

    while True:
        # Update queued_keys based on queue contents
        queued_keys = set()
        for a in queue:
            for k, desc in action_descriptions.items():
                if a["description"] == desc:
                    queued_keys.add(k)

        # Determine if subdomain/vhost check is allowed (only for hostnames)
        subdomain_allowed = not valid_ip(target)
        vhost_allowed = not valid_ip(target)

        print_green(f"[HTTP] Options for {target}:{port}")
        for action in actions:
            mark = " [*]" if action["key"] in queued_keys and action["key"] != "5" else ""
            if action["key"] == "2" and not subdomain_allowed:
                print_green(f"  {action['key']}. [unavailable for IPs] {action['desc']}")
            elif action["key"] == "3" and not vhost_allowed:
                print_green(f"  {action['key']}. [unavailable for IPs] {action['desc']}")
            else:
                print_green(f"  {action['key']}.{mark} {action['desc']}{mark}")

        choice = prompt_input("Select an option: ", "5")

        if choice in queued_keys and choice != "5":
            print_yellow("[*] That action is already queued. Please select another.")
            continue

        if choice == "1":
            queue.append({
                "description": action_descriptions["1"],
                "function": lambda: gobuster_scan(url)
            })
        elif choice == "2":
            if not subdomain_allowed:
                print_yellow("[*] Subdomain check is only available for hostnames, not IP addresses.")
                continue
            domain = target
            queue.append({
                "description": action_descriptions["2"],
                "function": lambda: gobuster_dns(domain)
            })
        elif choice == "3":
            if not vhost_allowed:
                print_yellow("[*] Vhost scan is only available for hostnames, not IP addresses.")
                continue
            domain = target
            queue.append({
                "description": action_descriptions["3"],
                "function": lambda: gobuster_vhost(domain)
            })
        elif choice == "4":
            queue.append({
                "description": action_descriptions["4"],
                "function": lambda: subprocess.run(["xdg-open", url])
            })
        elif choice == "5":
            print_green("[*] Done selecting actions for this port.")
            break
        else:
            print_yellow("[*] Invalid option, please select again.")
