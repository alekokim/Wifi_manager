from scapy.all import ARP, Ether, srp


def scan_network(network):
    print(f"\nScanning {network} ...")

    arp_request = ARP(pdst=network)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")

    packet = broadcast / arp_request

    answered = srp(packet, timeout=3, verbose=False)[0]

    devices = []

    for sent, received in answered:
        devices.append({
            "ip": received.psrc,
            "mac": received.hwsrc
        })

    return devices


def show_devices(devices):
    if not devices:
        print("\nNo devices found.")
        return

    print("\n===== DEVICES FOUND =====")

    for number, device in enumerate(devices, start=1):
        print(
            f"{number}. "
            f"IP: {device['ip']} | "
            f"MAC: {device['mac']}"
        )


if __name__ == "__main__":
    devices = scan_network("192.168.0.0/24")

    show_devices(devices)