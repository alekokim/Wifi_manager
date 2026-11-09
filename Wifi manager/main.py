from database.database import (
    create_database,
    add_network,
    delete_network,
    get_networks,
    get_network_by_id,
    get_saved_devices,
    get_device_by_id,
    get_events,
)

from wifi_connection import (
    connect_to_wifi,
    get_wifi_profiles,
)

from dashboard import show_dashboard


def show_networks():
    """Display saved Wi-Fi network configurations."""
    networks = get_networks()

    if not networks:
        print("\nNo Wi-Fi networks have been added yet.")
        return

    print("\n===== SAVED WI-FI NETWORKS =====")

    for network in networks:
        print(
            f"ID: {network[0]} | "
            f"Name: {network[1]} | "
            f"Router: {network[2]} | "
            f"Address: {network[3]}"
        )


def add_new_network():
    """Add a router configuration to the database."""
    print("\n===== ADD WI-FI NETWORK =====")

    name = input("Network name: ").strip()
    router_type = input("Router type: ").strip()
    router_url = input("Router address: ").strip()
    username = input("Router username: ").strip()
    password = input("Router password: ")

    if not name or not router_type or not router_url:
        print("\nNetwork name, router type, and address are required.")
        return

    try:
        add_network(
            name,
            router_type,
            router_url,
            username,
            password,
        )
        print("\nWi-Fi network added successfully!")

    except Exception as error:
        print(f"\nUnable to add network: {error}")


def delete_saved_network():
    """Delete a saved router configuration after confirmation."""
    networks = get_networks()

    if not networks:
        print("\nNo Wi-Fi networks have been added yet.")
        return

    print("\n===== DELETE WI-FI NETWORK =====")

    for network in networks:
        print(f"ID: {network[0]} | Name: {network[1]}")

    try:
        network_id = int(
            input("\nEnter the ID of the network to delete: ")
        )
    except ValueError:
        print("\nPlease enter a valid number.")
        return

    network = get_network_by_id(network_id)

    if not network:
        print("\nNetwork not found.")
        return

    confirmation = input(
        f"\nDelete '{network[1]}'? (y/N): "
    ).strip().lower()

    if confirmation not in ("y", "yes"):
        print("\nDeletion cancelled.")
        return

    try:
        if delete_network(network_id):
            print("\nWi-Fi network deleted successfully.")
        else:
            print("\nNetwork not found; nothing was deleted.")

    except Exception as error:
        print(f"\nUnable to delete network: {error}")


def connect_to_network():
    """Connect to a Wi-Fi profile saved in Windows."""
    profiles = get_wifi_profiles()

    if not profiles:
        print("\nNo saved Windows Wi-Fi profiles found.")
        print("Connect to a Wi-Fi network from Windows first.")
        return

    print("\n===== AVAILABLE WI-FI PROFILES =====")

    for number, profile in enumerate(profiles, start=1):
        print(f"{number}. {profile}")

    try:
        choice = int(
            input("\nChoose Wi-Fi profile number: ")
        )
    except ValueError:
        print("\nPlease enter a valid number.")
        return

    if choice < 1 or choice > len(profiles):
        print("\nInvalid profile number.")
        return

    network_name = profiles[choice - 1]

    print(f"\nSelected network: {network_name}")

    try:
        result = connect_to_wifi(network_name)

        if result is False:
            print("\nThe connection request failed.")
        else:
            print("\nConnection request sent.")
            print("Check Windows Wi-Fi status to confirm the connection.")

    except Exception as error:
        print(f"\nUnable to connect: {error}")


def check_connected_devices():
    """Scan the currently connected local network."""
    from network_scanner import (
        get_network_range,
        scan_network,
    )

    print("\n===== CHECK CONNECTED DEVICES =====")
    print("Detecting your current network...")

    try:
        network = get_network_range()
        print(f"Network detected: {network}")

        devices = scan_network(network)

        if not devices:
            print("\nNo devices responded to the scan.")
            return

        print("\n===== DEVICES FOUND =====")

        for device in devices:
            print(
                f"IP: {device.get('ip', 'Unknown')} | "
                f"MAC: {device.get('mac', 'Unknown')} | "
                f"Name: {device.get('name', 'Unknown Device')}"
            )

        print(f"\nTotal responding devices: {len(devices)}")

    except Exception as error:
        print("\nUnable to scan the network.")
        print(f"Error: {error}")


def monitor_network_menu():
    """Start the existing network monitoring module."""
    try:
        from monitoring import monitor_network
        monitor_network()

    except Exception as error:
        print("\nUnable to start network monitoring.")
        print(f"Error: {error}")


def show_device_history():
    """Display saved device records."""
    devices = get_saved_devices()

    if not devices:
        print("\nNo device history available yet.")
        print("Run Network Monitor first.")
        return

    print("\n===== DEVICE HISTORY =====")

    print(
        f"{'ID':<5}"
        f"{'Device Name':<22}"
        f"{'IP Address':<18}"
        f"{'MAC Address':<20}"
        f"{'Status':<12}"
    )

    print("-" * 77)

    for device in devices:
        print(
            f"{device[0]:<5}"
            f"{str(device[1]):<22}"
            f"{str(device[2]):<18}"
            f"{str(device[3]):<20}"
            f"{str(device[6]):<12}"
        )

        print(f"     First seen: {device[4]}")
        print(f"     Last seen:  {device[5]}")

        if len(device) > 7:
            print(f"     Network:    {device[7]}")

        print()


def show_device_details():
    """Display details for a selected saved device."""
    from network_scanner import (
        get_network_range,
        scan_network,
    )

    devices = get_saved_devices()

    if not devices:
        print("\nNo devices available.")
        return

    print("\n===== SELECT DEVICE =====")

    for device in devices:
        print(
            f"ID: {device[0]} | "
            f"Name: {device[1]} | "
            f"IP: {device[2]} | "
            f"Status: {device[6]}"
        )

    try:
        device_id = int(input("\nEnter device ID: "))
    except ValueError:
        print("\nPlease enter a valid number.")
        return

    device = get_device_by_id(device_id)

    if not device:
        print("\nDevice not found.")
        return

    print("\n================================")
    print("          DEVICE DETAILS")
    print("================================")
    print(f"ID          : {device[0]}")
    print(f"Device Name : {device[1]}")
    print(f"IP Address  : {device[2]}")
    print(f"MAC Address : {device[3]}")
    print(f"Saved Status: {device[6]}")
    print(f"First Seen  : {device[4]}")
    print(f"Last Seen   : {device[5]}")

    if len(device) > 7:
        print(f"Network     : {device[7]}")

    print("\nChecking live status...")

    try:
        network = get_network_range()
        live_devices = scan_network(network)

        is_online = any(
            item.get("ip") == device[2]
            for item in live_devices
        )

        print(
            f"\nLive Status  : "
            f"{'ONLINE' if is_online else 'NOT DETECTED'}"
        )

    except Exception as error:
        print("\nUnable to check live status.")
        print(f"Error: {error}")

    print("\n================================")


def show_event_history():
    """Display recorded network events."""
    events = get_events()

    if not events:
        print("\nNo network events recorded yet.")
        print("Run Network Monitor to create events.")
        return

    print("\n===== NETWORK EVENT HISTORY =====")

    for event in events:
        print("-" * 60)
        print(f"Event ID    : {event[0]}")
        print(f"Device Name : {event[1]}")
        print(f"IP Address  : {event[2]}")
        print(f"MAC Address : {event[3]}")
        print(f"Event       : {event[4]}")
        print(f"Time        : {event[5]}")

        if len(event) > 6:
            print(f"Network     : {event[6]}")

    print("-" * 60)


def main():
    """Run the Wi-Fi Manager menu."""
    try:
        create_database()
    except Exception as error:
        print(f"Unable to initialize the database: {error}")
        return

    while True:
        print("\n" + "=" * 38)
        print("           WI-FI MANAGER")
        print("=" * 38)
        print("1. Network Dashboard")
        print("2. Add Wi-Fi network")
        print("3. View Wi-Fi networks")
        print("4. Connect to a network")
        print("5. Check connected devices")
        print("6. Monitor network")
        print("7. View device history")
        print("8. View device details")
        print("9. View event history")
        print("10. Delete Wi-Fi network")
        print("11. Exit")
        print("=" * 38)

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            try:
                show_dashboard()
            except Exception as error:
                print(f"\nUnable to open dashboard: {error}")

        elif choice == "2":
            add_new_network()

        elif choice == "3":
            show_networks()

        elif choice == "4":
            connect_to_network()

        elif choice == "5":
            check_connected_devices()

        elif choice == "6":
            monitor_network_menu()

        elif choice == "7":
            show_device_history()

        elif choice == "8":
            show_device_details()

        elif choice == "9":
            show_event_history()

        elif choice == "10":
            delete_saved_network()

        elif choice == "11":
            print("\nWi-Fi Manager closed.")
            break

        else:
            print("\nInvalid option. Enter a number from 1 to 11.")


if __name__ == "__main__":
    main()