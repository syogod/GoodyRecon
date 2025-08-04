from handlers import http

def handle_port(target, port, service, queue, host_override):
    print(f"\n[+] Detected open port {port}/tcp ({service})")
    if service in ["http", "http-alt", "https"]:
        http.handle_http(target, port, queue, host_override)
    else:
        print(f"[!] No handler for service: {service}")

def execute_queue(queue):
    print("\n[+] Executing queued actions...\n")
    for action in queue:
        print(f"[~] {action['description']}")
        try:
            action['function']()
        except Exception as e:
            print(f"[!] Error running action: {e}")
