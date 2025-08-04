from scanner import run_nmap_scan, parse_nmap_output
from port_handler import handle_port, execute_queue
from utils import print_green, print_yellow, print_red, prompt_input

def main():

    target = prompt_input("Enter the target IP or hostname: ", False).strip()
    nmap_output = run_nmap_scan(target)
    print(nmap_output)

    open_ports = parse_nmap_output(nmap_output)
    action_queue = []   # queue of actions to be taken for each open port
    host_override = {}

    for port, service in open_ports:
        handle_port(target, port, service, action_queue, host_override)

    if not action_queue:
        print("\n[*] No actions selected. Exiting.")
        return

    print("\nQueued Actions:")
    for i, action in enumerate(action_queue, 1):
        print_green(f"  {i}. {action['description']}")

    confirm = prompt_input("\nRun all actions? [Y/n]: ", "Y").lower()
    if confirm == 'y':
        execute_queue(action_queue)
    else:
        print("[*] Execution cancelled.")

if __name__ == "__main__":
    main()
