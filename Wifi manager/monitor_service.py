import threading
import time
from datetime import datetime

from database.database import (
    save_device,
    update_device_status,
    add_event,
    get_saved_devices
)

from network_scanner import (
    get_network_details,
    scan_network
)

from email_alerts import (
    send_email_alert
)


class NetworkMonitor:

    def __init__(self, interval=30):

        self.interval = interval
        self.running = False
        self.thread = None

        self.previous_devices = set()

        # Network currently being monitored
        self.current_network = None

        self.callbacks = []

    # =====================================================
    # CALLBACK
    # =====================================================

    def add_callback(self, callback):

        self.callbacks.append(callback)

    def notify(self, message):

        for callback in self.callbacks:

            try:
                callback(message)

            except Exception:
                pass

    # =====================================================
    # GET CURRENT NETWORK
    # =====================================================

    def get_current_network(self):

        try:

            details = get_network_details()

            return details

        except Exception as error:

            self.notify(
                f"Unable to determine network: {error}"
            )

            return None

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self.monitor_loop,
            daemon=True
        )

        self.thread.start()

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):

        self.running = False

    # =====================================================
    # MONITOR LOOP
    # =====================================================

    def monitor_loop(self):

        details = self.get_current_network()

        if not details:

            self.running = False
            return

        self.current_network = details["network"]

        self.notify(
            f"Monitoring started: {self.current_network}"
        )

        # =================================================
        # INITIAL SCAN
        # =================================================

        try:

            devices = scan_network(
                self.current_network
            )

            self.previous_devices = {
                device["mac"].lower()
                for device in devices
            }

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
                    status="ONLINE",
                    network=self.current_network
                )

            self.notify(
                f"Initial scan complete: "
                f"{len(devices)} device(s) online"
            )

        except Exception as error:

            self.notify(
                f"Initial scan error: {error}"
            )

        # =================================================
        # CONTINUOUS MONITORING
        # =================================================

        while self.running:

            try:

                details = self.get_current_network()

                if not details:

                    time.sleep(5)
                    continue

                detected_network = details["network"]

                # =========================================
                # NETWORK CHANGED
                # =========================================

                if detected_network != self.current_network:

                    old_network = self.current_network

                    self.notify(
                        "================================"
                    )

                    self.notify(
                        "NETWORK CHANGE DETECTED"
                    )

                    self.notify(
                        f"Old network: {old_network}"
                    )

                    self.notify(
                        f"New network: {detected_network}"
                    )

                    # Clear devices being tracked
                    # for the old network
                    self.previous_devices = set()

                    # Switch network
                    self.current_network = detected_network

                    self.notify(
                        "Old current devices cleared."
                    )

                    self.notify(
                        f"Now monitoring: "
                        f"{self.current_network}"
                    )

                    # Scan new network
                    devices = scan_network(
                        self.current_network
                    )

                    self.previous_devices = {
                        device["mac"].lower()
                        for device in devices
                    }

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
                            status="ONLINE",
                            network=self.current_network
                        )

                    self.notify(
                        f"New network scan complete: "
                        f"{len(devices)} device(s) online"
                    )

                    self.notify(
                        "================================"
                    )

                    # Wait before next scan
                    for _ in range(self.interval):

                        if not self.running:
                            break

                        time.sleep(1)

                    continue

                # =========================================
                # NORMAL SCAN
                # =========================================

                devices = scan_network(
                    self.current_network
                )

                current_time = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                current_devices = {
                    device["mac"].lower(): device
                    for device in devices
                }

                current_macs = set(
                    current_devices.keys()
                )

                # =========================================
                # NEW DEVICES
                # =========================================

                new_devices = (
                    current_macs
                    - self.previous_devices
                )

                # =========================================
                # DISCONNECTED DEVICES
                # =========================================

                disconnected_devices = (
                    self.previous_devices
                    - current_macs
                )

                # =========================================
                # SAVE CURRENT DEVICES
                # =========================================

                for device in devices:

                    save_device(
                        device_name=device["name"],
                        ip_address=device["ip"],
                        mac_address=device["mac"],
                        first_seen=current_time,
                        last_seen=current_time,
                        status="ONLINE",
                        network=self.current_network
                    )

                # =========================================
                # NEW DEVICE ALERT
                # =========================================

                for mac in new_devices:

                    device = current_devices[mac]

                    add_event(
                        device_name=device["name"],
                        ip_address=device["ip"],
                        mac_address=device["mac"],
                        event_type="DEVICE_ONLINE",
                        event_time=current_time,
                        network=self.current_network
                    )

                    message = (
                        "A new device has connected "
                        "to your Wi-Fi network.\n\n"

                        f"Device Name: {device['name']}\n"
                        f"IP Address: {device['ip']}\n"
                        f"MAC Address: {device['mac']}\n"
                        f"Network: {self.current_network}\n"
                        f"Time: {current_time}"
                    )

                    send_email_alert(
                        subject="Wi-Fi Manager - New Device Connected",
                        message=message
                    )

                    self.notify(
                        f"NEW DEVICE: "
                        f"{device['ip']} "
                        f"{device['mac']}"
                    )

                # =========================================
                # DISCONNECTED DEVICE
                # =========================================

                saved_devices = get_saved_devices()

                for mac in disconnected_devices:

                    for device in saved_devices:

                        # device[3] = MAC
                        # device[7] = network

                        if (
                            device[3].lower() == mac
                            and device[7] == self.current_network
                        ):

                            update_device_status(
                                mac_address=device[3],
                                status="OFFLINE",
                                network=self.current_network
                            )

                            add_event(
                                device_name=device[1],
                                ip_address=device[2],
                                mac_address=device[3],
                                event_type="DEVICE_OFFLINE",
                                event_time=current_time,
                                network=self.current_network
                            )

                            message = (
                                "A device has disconnected "
                                "from your Wi-Fi network.\n\n"

                                f"Device Name: {device[1]}\n"
                                f"IP Address: {device[2]}\n"
                                f"MAC Address: {device[3]}\n"
                                f"Network: {self.current_network}\n"
                                f"Time: {current_time}"
                            )

                            send_email_alert(
                                subject="Wi-Fi Manager - Device Disconnected",
                                message=message
                            )

                            self.notify(
                                f"DEVICE OFFLINE: "
                                f"{device[2]} "
                                f"{device[3]}"
                            )

                            break

                # =========================================
                # UPDATE PREVIOUS DEVICES
                # =========================================

                self.previous_devices = current_macs

                self.notify(
                    f"Scan complete: "
                    f"{len(devices)} device(s) online"
                )

            except Exception as error:

                self.notify(
                    f"Monitoring error: {error}"
                )

            # =========================================
            # WAIT
            # =========================================

            for _ in range(self.interval):

                if not self.running:
                    break

                time.sleep(1)

        self.notify(
            "Monitoring stopped."
        )