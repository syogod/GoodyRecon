from scanner import run_nmap_scan, parse_nmap_output
from port_handler import handle_port, execute_queue
from utils import print_green, print_yellow, print_red, prompt_input

def main():
    # Prompt user for the target IP or hostname
    target = prompt_input("Enter the target IP or hostname: ", False).strip()
    # Run nmap scan on the target
    nmap_output = run_nmap_scan(target)
    print(nmap_output)

    # Parse nmap output to get list of open ports and their services
    open_ports = parse_nmap_output(nmap_output)
    action_queue = []   # queue of actions to be taken for each open port
    host_override = {}  # dictionary for host overrides if needed

    # For each open port, handle possible actions and add to queue
    for port, service in open_ports:
        handle_port(target, port, service, action_queue, host_override)

    # If no actions were selected, exit
    if not action_queue:
        print("\n[*] No actions selected. Exiting.")
        return

    # Display queued actions to the user
    print("\nQueued Actions:")
    for i, action in enumerate(action_queue, 1):
        print_green(f"  {i}. {action['description']}")

    # Prompt user to confirm execution of all actions
    confirm = prompt_input("\nRun all actions? [Y/n]: ", "Y").lower()
    if confirm == 'y':
        execute_queue(action_queue)  # Execute all queued actions
    else:
        print("[*] Execution cancelled.")

if __name__ == "__main__":
    main()
