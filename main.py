from scanner import run_nmap_scan, parse_nmap_output
from port_handler import handle_port, execute_queue

def main():
    target = input("Enter the target IP or hostname: ").strip()
    nmap_output = run_nmap_scan(target)
    print(nmap_output)

    open_ports = parse_nmap_output(nmap_output)
    action_queue = []

    for port, service in open_ports:
        handle_port(target, port, service, action_queue)

    if not action_queue:
        print("\n[*] No actions selected. Exiting.")
        return

    print("\nQueued Actions:")
    for i, action in enumerate(action_queue, 1):
        print(f"  {i}. {action['description']}")

    confirm = input("\nRun all actions? [y/N]: ").lower()
    if confirm == 'y':
        execute_queue(action_queue)
    else:
        print("[*] Execution cancelled.")

if __name__ == "__main__":
    main()
