import requests
from urllib.parse import urlparse
import re
import os
import subprocess
import hashlib

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
        "gobuster", "dir",
        "-u", url,
        "-w", "/usr/share/wordlists/dirb/common.txt"
    ]
    if follow_redirects:
        args.append("-r")
    if exclude_length:
        args += ["--exclude-length", str(exclude_length)]

    print(f"[~] Running Gobuster{' with -r' if follow_redirects else ''}: {url}")
    result = subprocess.run(args, capture_output=True, text=True)

    # Check stderr for specific 302 error
    stderr = result.stderr
    if ("Error: the server returns a status code that matches the provided options" in stderr and
        "=> 302" in stderr):
        if not follow_redirects:
            print("[!] Gobuster failed due to 302 redirects.")
            print("[~] Retrying with -r (follow redirects)...")
            return gobuster_scan(url, follow_redirects=True)
        else:
            print("[!] Gobuster still failed even with -r:")
            print(stderr)
    elif "Error: the server returns a status code that matches the provided options" in stderr:
        print("[!] Gobuster encountered a soft 404 behavior (e.g., 200s).")
        print("[~] You'll need to manually tune status codes or lengths.")
        print(stderr)
    else:
        print(result.stdout)


def get_protocol_and_url(target, port, service):
    # crude but effective
    service = service.lower()
    if "https" in service or "ssl" in service:
        protocol = "https"
    else:
        protocol = "http"
    url = f"{protocol}://{target}:{port}"
    return protocol, url


def check_redirect_and_offer_hosts_entry(url, ip):
    try:
        print(f"[*] Checking for 302 redirect on {url}...")
        response = requests.get(url, allow_redirects=False, timeout=5, verify=False)
        if response.status_code == 302:
            location = response.headers.get("Location", "")
            parsed = urlparse(location)

            if parsed.hostname and not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", parsed.hostname):
                print(f"[!] Detected redirect to: {parsed.hostname}")
                add = input(f"Add '{parsed.hostname} {ip}' to /etc/hosts? [y/N]: ").lower()
                if add == 'y':
                    with open("/etc/hosts", "a") as f:
                        f.write(f"\n{ip} {parsed.hostname}")
                    print("[+] Entry added to /etc/hosts.")
                else:
                    print("[*] Skipped /etc/hosts entry.")
                return parsed.hostname
        else:
            print(f"[*] No redirect found. Status: {response.status_code}")
    except Exception as e:
        print(f"[!] Error checking redirect: {e}")
    return None

def handle_http(target, port, queue, host_override, service="http"):
    protocol, url = get_protocol_and_url(target, port, service)

    hostname = check_redirect_and_offer_hosts_entry(target, port)
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
