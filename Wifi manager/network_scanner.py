
import socket
import subprocess
import ipaddress
import re

from scapy.all import (
    ARP,
    Ether,
    srp,
    conf,
    get_if_list,
    get_if_addr,
    get_if_hwaddr,
)


def get_local_ip():
    """Detect the IPv4 address used by the active network."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
    except OSError as error:
        raise RuntimeError(
            f"Could not detect the active network IP: {error}"
        ) from error
    finally:
        sock.close()

    if local_ip.startswith("127."):
        raise RuntimeError("No active network connection detected.")

    return local_ip


def get_network_details():
    """Get the current IP, subnet, gateway, and network range."""
    local_ip = get_local_ip()

    result = subprocess.run(
        ["ipconfig"],
        capture_output=True,
        text=True,
        encoding="mbcs",
        errors="replace",
        timeout=10,
    )

    if result.returncode != 0:
        raise RuntimeError("Could not read Windows network settings.")

    sections = re.split(r"\r?\n\s*\r?\n", result.stdout)
    subnet_mask = None
    gateway = None

    for section in sections:
        if not re.search(
            r"(?<![\d.])" + re.escape(local_ip) + r"(?![\d.])",
            section,
        ):
            continue

        mask_match = re.search(
            r"Subnet Mask[ .:]+(\d{1,3}(?:\.\d{1,3}){3})",
            section,
            re.IGNORECASE,
        )
        gateway_match = re.search(
            r"Default Gateway[ .:]+(\d{1,3}(?:\.\d{1,3}){3})",
            section,
            re.IGNORECASE,
        )

        if mask_match:
            subnet_mask = mask_match.group(1)

        if gateway_match:
            gateway = gateway_match.group(1)

        break

    if not subnet_mask:
        raise RuntimeError(
            "Subnet mask not found. Run ipconfig in PowerShell "
            "and check the active Wi-Fi adapter."
        )

    try:
        network = ipaddress.ip_network(
            f"{local_ip}/{subnet_mask}",
            strict=False,
        )
    except ValueError as error:
        raise RuntimeError(
            f"Invalid network configuration: {error}"
        ) from error

    return {
        "local_ip": local_ip,
        "subnet_mask": subnet_mask,
        "gateway": gateway or "Unknown",
        "network": str(network),
        "network_address": str(network.network_address),
        "broadcast": str(network.broadcast_address),
        "prefix_length": network.prefixlen,
    }


def get_network_range():
    """Return the current network range in CIDR format."""
    return get_network_details()["network"]


def get_network_interface(network=None):
    """Find the Scapy interface matching the active local IP."""
    local_ip = get_local_ip()

    for interface in get_if_list():
        try:
            if get_if_addr(interface) == local_ip:
                return interface
        except Exception:
            continue

    raise RuntimeError(
        f"No Scapy interface matches IP {local_ip}. "
        "Check that Npcap is installed and the correct Wi-Fi "
        "adapter is active."
    )


def get_device_name(ip_address):
    """Try to resolve a device name; it may remain unknown."""
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]

        if hostname and hostname != ip_address:
            return hostname
    except (socket.herror, socket.gaierror, OSError):
        pass

    try:
        result = subprocess.run(
            ["nbtstat", "-A", ip_address],
            capture_output=True,
            text=True,
            timeout=3,
            errors="replace",
        )

        for line in result.stdout.splitlines():
            if "<00>" in line and "UNIQUE" in line.upper():
                parts = line.split()

                if parts and parts[0] != ip_address:
                    return parts[0]

    except (subprocess.SubprocessError, OSError):
        pass

    return "Unknown Device"


def scan_network(network=None):
    """
    Scan the laptop's current local network using ARP.

    Only scans the active local subnet. The network argument is
    checked against the active subnet to avoid scanning unrelated
    networks from this function.
    """
    details = get_network_details()
    local_ip = details["local_ip"]
    local_network = ipaddress.ip_network(
        f"{local_ip}/{details['subnet_mask']}",
        strict=False,
    )

    if network is None:
        target_network = local_network
    else:
        try:
            target_network = ipaddress.ip_network(
                network,
                strict=False,
            )
        except ValueError as error:
            raise RuntimeError(
                f"Invalid network range: {error}"
            ) from error

    if target_network != local_network:
        raise RuntimeError(
            f"Requested network {target_network} does not match "
            f"the currently connected network {local_network}. "
            "Connect to that Wi-Fi before scanning it."
        )

    if target_network.num_addresses > 4096:
        raise RuntimeError("This network is too large to scan.")

    interface = get_network_interface()
    interface_mac = get_if_hwaddr(interface)

    print("\n" + "=" * 50)
    print("CURRENT NETWORK")
    print("=" * 50)
    print(f"Local IP      : {local_ip}")
    print(f"Subnet Mask   : {details['subnet_mask']}")
    print(f"Gateway       : {details['gateway']}")
    print(f"Network       : {target_network}")
    print(f"Interface     : {interface}")
    print(f"Interface MAC : {interface_mac}")
    print("=" * 50)

    try:
        conf.iface = interface

        packet = (
            Ether(
                src=interface_mac,
                dst="ff:ff:ff:ff:ff:ff",
            )
            / ARP(
                pdst=str(target_network),
                psrc=local_ip,
                hwsrc=interface_mac,
            )
        )

        print("Scanning the current local network...")

        answered = srp(
            packet,
            iface=interface,
            timeout=5,
            verbose=False,
        )[0]

    except Exception as error:
        raise RuntimeError(
            f"Network scan failed: {error}. "
            "Check Npcap, permissions, and your Wi-Fi adapter."
        ) from error

    devices_by_mac = {}

    for sent, received in answered:
        mac_address = received.hwsrc.lower()

        devices_by_mac[mac_address] = {
            "ip": received.psrc,
            "mac": received.hwsrc,
            "name": "Unknown Device",
        }

    devices = list(devices_by_mac.values())

    for device in devices:
        device["name"] = get_device_name(device["ip"])

    print(f"\nScan complete: {len(devices)} device(s) responded.")

    return devices


if __name__ == "__main__":
    print("Wi-Fi Manager - Network Scanner")

    try:
        details = get_network_details()

        print("\nNETWORK DETAILS")
        print("-" * 40)
        print(f"Local IP      : {details['local_ip']}")
        print(f"Subnet Mask   : {details['subnet_mask']}")
        print(f"Gateway       : {details['gateway']}")
        print(f"Network       : {details['network']}")
        print(f"Broadcast     : {details['broadcast']}")
        print(f"Prefix Length : /{details['prefix_length']}")

        devices = scan_network(details["network"])

        print("\nDEVICES FOUND")
        print("-" * 70)

        for device in devices:
            print(
                f"{device['ip']} | "
                f"{device['mac']} | "
                f"{device['name']}"
            )

        print("-" * 70)
        print(f"Total devices found: {len(devices)}")

    except Exception as error:
        print(f"\nERROR: {error}")
