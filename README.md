# GoodyRecon

GoodyRecon is an automated reconnaissance tool designed to help security professionals and enthusiasts quickly enumerate open ports and services on a target, and perform further actions such as directory brute-forcing, subdomain enumeration, vhost scanning, robots.txt checking, and HTTP analysis.

## Features

- Runs Nmap scans to detect open ports and services
- Parses Nmap output to identify actionable services
- Interactive queue system for post-scan actions
- HTTP/HTTPS handler with options for:
  - Gobuster directory brute-forcing (with soft 404 detection)
  - Subdomain enumeration (Gobuster DNS mode)
  - Vhost enumeration (Gobuster vhost mode)
  - robots.txt checking and output display
  - Browser opening
- Handles soft 404 detection and offers to update `/etc/hosts` for redirecting hosts

## Requirements

- Python 3.x
- [nmap](https://nmap.org/) installed and in your PATH
- [gobuster](https://github.com/OJ/gobuster) installed and in your PATH
- [colorama](https://pypi.org/project/colorama/) Python package
- Linux environment (for `/etc/hosts` manipulation and `xdg-open`)
- Wordlists:
  - `/usr/share/wordlists/dirb/common.txt`
  - `/usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-20000.txt`

## Usage

1. Clone or copy the GoodyRecon files to your machine.
2. Run the main script:

   ```bash
   python3 main.py
   ```

3. Follow the prompts to enter a target IP or hostname.
4. Select actions for each detected service as prompted.

## Notes

- Some actions (like updating `/etc/hosts`) may require root privileges.
- Subdomain and vhost checks are only available for hostnames, not IP addresses.
- Ensure the required wordlists are present at the specified paths.

## Disclaimer

This tool is intended for authorized testing and educational purposes only. Always have permission before scanning or testing any network or system.
