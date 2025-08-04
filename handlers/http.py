import subprocess

def handle_http(target, port, queue):
    print(f"[HTTP] Options for {target}:{port}")
    print("  1. Queue gobuster for directories")
    print("  2. Queue subdomain check")
    print("  3. Queue browser open")
    print("  4. Skip")
    choice = input("Select an option: ")

    url = f"http://{target}:{port}"

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
