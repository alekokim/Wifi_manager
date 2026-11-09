from datetime import datetime

from network_scanner import (
    get_local_ip,
    get_network_range,
    get_network_interface,
    scan_network
)

from database.database import (
    save_device
)


def get_dashboard_data():

    local_ip = get_local_ip()

    network = get_network_range()

    interface = get_network_interface(network)

    devices = scan_network(network)

    return {
        "local_ip": local_ip,
        "network": network,
        "interface": interface,
        "devices": devices
    }


def save_scanned_devices(devices):

    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    for device in devices:

        save_device(
            device_name=device["name"],
            ip_address=device["ip"],
            mac_address=device["mac"],
            first_seen=current_time,
            last_seen=current_time,
            status="ONLINE"
        )


def show_dashboard():

    print("\n========================================")
    print("             NETWORK DASHBOARD")
    print("========================================")

    print("\nDetecting network information...")

    try:

        data = get_dashboard_data()

        local_ip = data["local_ip"]

        network = data["network"]

        interface = data["interface"]

        devices = data["devices"]

        # Save detected devices
        save_scanned_devices(devices)

        # Calculate statistics
        total_devices = len(devices)

        unknown_devices = sum(
            1
            for device in devices
            if device["name"] == "Unknown"
        )

        known_devices = (
            total_devices - unknown_devices
        )

        print(
            "\n----------- NETWORK INFORMATION -----------"
        )

        print(
            f"Local IP       : {local_ip}"
        )

        print(
            f"Network        : {network}"
        )

        print(
            f"Interface      : {interface}"
        )

        print(
            f"Devices Online : {total_devices}"
        )

        print(
            f"Known Devices  : {known_devices}"
        )

        print(
            f"Unknown Devices: {unknown_devices}"
        )

        print(
            "\n--------------- DEVICES ------------------"
        )

        if not devices:

            print("No devices detected.")

        else:

            print(
                f"{'No.':<5}"
                f"{'Device Name':<25}"
                f"{'IP Address':<18}"
                f"{'MAC Address':<20}"
            )

            print("-" * 68)

            for number, device in enumerate(
                devices,
                start=1
            ):

                print(
                    f"{number:<5}"
                    f"{device['name']:<25}"
                    f"{device['ip']:<18}"
                    f"{device['mac']:<20}"
                )

        print(
            "\n========================================"
        )

        print("Network status: ONLINE")

        print(
            "========================================"
        )

    except Exception as error:

        print(
            "\nUnable to load dashboard."
        )

        print(
            f"Error: {error}"
        )