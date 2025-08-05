from handlers import http
from utils import print_green, print_yellow, print_red, prompt_input

def handle_port(target, port, service, queue, host_override):
    # Handle an open port by dispatching to the appropriate service handler
    print_green(f"\n[+] Detected open port {port}/tcp ({service})")
    if "http" in service:
        http.handle_http(target, port, queue, host_override, service)
    else:
        print(f"[!] No handler for service: {service}")

def execute_queue(queue):
    # Execute all actions in the queue sequentially
    print_green("\n[+] Executing queued actions...\n")
    for action in queue:
        print_green(f"[~] {action['description']}")
        try:
            action['function']()
        except Exception as e:
            print_red(f"[!] Error running action: {e}")
