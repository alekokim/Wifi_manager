import time
from datetime import datetime

from network_scanner import (
    get_network_range,
    scan_network
)

from database.database import (
    save_device,
    update_device_status,
    get_saved_devices,
    add_event
)


def monitor_network():

    print("\n===== NETWORK MONITOR =====")

    network = get_network_range()

    print(f"Monitoring network: {network}")
    print("Press Ctrl+C to stop monitoring.\n")

    # Load devices already known by the database
    saved_devices = get_saved_devices()

    previous_devices = {
        device[3]
        for device in saved_devices
        if device[6] == "ONLINE"
    }

    first_scan = True

    try:

        while True:

            devices = scan_network(network)

            current_devices = {
                device["mac"]
                for device in devices
            }

            new_devices = (
                current_devices - previous_devices
            )

            disconnected_devices = (
                previous_devices - current_devices
            )

            current_time = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # Save currently online devices
            for device in devices:

                save_device(
                    device_name=device["name"],
                    ip_address=device["ip"],
                    mac_address=device["mac"],
                    first_seen=current_time,
                    last_seen=current_time,
                    status="ONLINE"
                )

            # Record new devices
            for device in devices:

                if device["mac"] in new_devices:

                    add_event(
                        device_name=device["name"],
                        ip_address=device["ip"],
                        mac_address=device["mac"],
                        event_type="DEVICE_ONLINE",
                        event_time=current_time
                    )

            # Refresh database devices
            saved_devices = get_saved_devices()

            # Mark disconnected devices OFFLINE
            for mac in disconnected_devices:

                update_device_status(
                    mac_address=mac,
                    status="OFFLINE"
                )

                for saved_device in saved_devices:

                    if saved_device[3] == mac:

                        add_event(
                            device_name=saved_device[1],
                            ip_address=saved_device[2],
                            mac_address=saved_device[3],
                            event_type="DEVICE_OFFLINE",
                            event_time=current_time
                        )

                        break

            # Show newly detected devices
            if new_devices:

                print("\n" + "=" * 50)

                print("           NEW DEVICE DETECTED")

                print("=" * 50)

                for device in devices:

                    if device["mac"] in new_devices:

                        print(
                            f"Device Name : {device['name']}"
                        )

                        print(
                            f"IP Address  : {device['ip']}"
                        )

                        print(
                            f"MAC Address : {device['mac']}"
                        )

                        print("-" * 50)

            # Show devices that went offline
            if disconnected_devices:

                print("\n" + "=" * 50)

                print("           DEVICE OFFLINE")

                print("=" * 50)

                for mac in disconnected_devices:

                    print(
                        f"MAC Address : {mac}"
                    )

                print("=" * 50)

            # Display normal monitoring status
            if (
                not new_devices
                and not disconnected_devices
            ):

                print(
                    f"\n[{current_time}] "
                    f"{len(devices)} "
                    f"device(s) ONLINE."
                )

            if first_scan:

                print(
                    f"\nInitial scan complete: "
                    f"{len(devices)} "
                    f"device(s) detected."
                )

                first_scan = False

            previous_devices = current_devices

            print(
                "\nNext scan in 30 seconds..."
            )

            time.sleep(30)

    except KeyboardInterrupt:

        print(
            "\n\nNetwork monitoring stopped."
        )