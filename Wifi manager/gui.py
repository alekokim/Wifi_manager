import tkinter as tk
from tkinter import colorchooser, messagebox, ttk
from datetime import datetime

from database.database import (
    create_database,
    save_device,
    get_saved_devices,
    get_events
)

from network_scanner import (
    get_network_details,
    scan_network
)

from monitor_service import NetworkMonitor


class WifiManagerGUI:

    def __init__(self, root):

        self.root = root

        self.root.title("Wi-Fi Manager System")

        self.root.geometry("1150x720")
        self.background_color = "#ffffff"
        self.text_color = "#111827"
        self.style = ttk.Style(self.root)

        # Create database
        create_database()

        # Current network
        self.current_network = None

        # Current devices only
        self.current_devices = []

        # Monitoring object
        self.monitor = NetworkMonitor(
            interval=30
        )

        self.monitor.add_callback(
            self.monitor_message
        )

        # GUI references
        self.content_frame = None
        self.monitor_text = None
        self.device_table = None

        self.create_interface()

        self.show_dashboard()

    # =====================================================
    # CREATE MAIN INTERFACE
    # =====================================================

    def create_interface(self):

        # -----------------------------
        # SIDEBAR
        # -----------------------------

        self.sidebar = tk.Frame(
            self.root,
            width=230,
            bg="#1f2937"
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        title = tk.Label(
            self.sidebar,
            text="WI-FI MANAGER",
            font=("Arial", 17, "bold"),
            bg="#1f2937",
            fg="white"
        )

        title.pack(
            pady=25
        )

        tk.Button(
            self.sidebar,
            text="🎨  Background color",
            command=self.choose_background_color,
            bg="#374151",
            fg="white",
            relief="flat",
            pady=7
        ).pack(
            fill="x",
            padx=8,
            pady=(0, 12)
        )

        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Connected Devices", self.show_devices),
            ("Device Details", self.show_device_details),
            ("Device History", self.show_device_history),
            ("Event History", self.show_event_history),
            ("Network Scan", self.show_network_scan),
            ("Network Monitoring", self.show_monitoring),
            ("Exit", self.exit_application)
        ]

        for text, command in buttons:

            button = tk.Button(
                self.sidebar,
                text=text,
                width=24,
                command=command,
                bg="#374151",
                fg="white",
                relief="flat",
                pady=7
            )

            button.pack(
                pady=4
            )

        # -----------------------------
        # CONTENT AREA
        # -----------------------------

        self.content_frame = tk.Frame(
            self.root,
            bg=self.background_color
        )

        self.content_frame.pack(
            side="right",
            fill="both",
            expand=True
        )

    def choose_background_color(self):
        """Let the user choose a background color for the content area."""
        selected_color = colorchooser.askcolor(
            color=self.background_color,
            title="Choose background color",
            parent=self.root,
        )[1]

        if not selected_color:
            return

        red, green, blue = (
            int(selected_color[index:index + 2], 16) / 255
            for index in (1, 3, 5)
        )
        luminance = (
            0.2126 * red + 0.7152 * green + 0.0722 * blue
        )
        self.text_color = "#111827" if luminance > 0.45 else "#ffffff"
        self.background_color = selected_color

        self.content_frame.configure(bg=self.background_color)
        self._apply_content_colors(self.content_frame)
        self.style.configure(
            "Treeview",
            background=self.background_color,
            fieldbackground=self.background_color,
            foreground=self.text_color,
        )

    def _apply_content_colors(self, widget):
        if isinstance(widget, (tk.Frame, tk.Label, tk.LabelFrame, tk.Text)):
            widget.configure(bg=self.background_color)

            if isinstance(widget, (tk.Label, tk.LabelFrame, tk.Text)):
                widget.configure(fg=self.text_color)

        for child in widget.winfo_children():
            self._apply_content_colors(child)

    # =====================================================
    # CLEAR CONTENT
    # =====================================================

    def clear_content(self):

        for widget in self.content_frame.winfo_children():

            widget.destroy()

        self.monitor_text = None
        self.device_table = None

    # =====================================================
    # GET CURRENT NETWORK
    # =====================================================

    def get_current_network(self):

        try:

            return get_network_details()

        except Exception as error:

            messagebox.showerror(
                "Network Error",
                str(error)
            )

            return None

    # =====================================================
    # DASHBOARD
    # =====================================================

    def show_dashboard(self):

        self.clear_content()

        title = tk.Label(
            self.content_frame,
            text="Wi-Fi Manager Dashboard",
            font=("Arial", 24, "bold"),
            bg=self.background_color
        )

        title.pack(
            pady=25
        )

        details = self.get_current_network()

        if not details:
            return

        self.current_network = details["network"]

        # -----------------------------
        # NETWORK INFORMATION
        # -----------------------------

        network_frame = tk.LabelFrame(
            self.content_frame,
            text="Current Network",
            font=("Arial", 12, "bold"),
            bg=self.background_color,
            padx=20,
            pady=15
        )

        network_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )

        information = [
            ("Local IP", details.get("ip", "192.168.0.108")),
            ("Subnet Mask", details.get("subnet_mask", "255.255.255.0")),
            ("Gateway", details.get("gateway", "192.168.0.1")),
            ("Network Name", details.get("name", "Home-Tenda")),
            ("Broadcast", details.get("broadcast", "192.168.0.255"))
        ]

        for name, value in information:

            row = tk.Frame(
                network_frame,
                bg=self.background_color
            )

            row.pack(
                fill="x",
                pady=3
            )

            tk.Label(
                row,
                text=f"{name}:",
                width=18,
                anchor="e",
                font=("Arial", 10, "bold"),
                bg=self.background_color
            ).pack(
                side="left"
            )

            tk.Label(
                row,
                text=value,
                anchor="w",
                bg=self.background_color
            ).pack(
                side="left",
                padx=10
            )

        # -----------------------------
        # CURRENT DEVICE COUNT
        # -----------------------------

        device_frame = tk.LabelFrame(
            self.content_frame,
            text="Current Devices",
            font=("Arial", 12, "bold"),
            bg=self.background_color,
            padx=20,
            pady=20
        )

        device_frame.pack(
            fill="x",
            padx=30,
            pady=15
        )

        count_label = tk.Label(
            device_frame,
            text=f"{len(self.current_devices)} device(s)",
            font=("Arial", 20, "bold"),
            bg=self.background_color
        )

        count_label.pack()

        # -----------------------------
        # BUTTONS
        # -----------------------------

        button_frame = tk.Frame(
            self.content_frame,
            bg=self.background_color
        )

        button_frame.pack(
            pady=20
        )

        tk.Button(
            button_frame,
            text="Scan Current Network",
            width=25,
            command=self.scan_current_network
        ).pack(
            side="left",
            padx=10
        )

        tk.Button(
            button_frame,
            text="View Connected Devices",
            width=25,
            command=self.show_devices
        ).pack(
            side="left",
            padx=10
        )

    # =====================================================
    # SCAN CURRENT NETWORK
    # =====================================================

    def scan_current_network(self):

        details = self.get_current_network()

        if not details:
            return

        new_network = details["network"]

        # Detect network change
        if (
            self.current_network is not None
            and self.current_network != new_network
        ):

            self.current_devices = []

            messagebox.showinfo(
                "Network Changed",
                "A different network was detected.\n\n"
                "The previous current device list has been cleared."
            )

        self.current_network = new_network

        try:

            devices = scan_network(
                self.current_network
            )

        except Exception as error:

            messagebox.showerror(
                "Scan Error",
                str(error)
            )

            return

        # Store ONLY current devices
        self.current_devices = devices

        current_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Save devices with network
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

        messagebox.showinfo(
            "Scan Complete",
            f"{len(devices)} device(s) found.\n\n"
            f"Network: {self.current_network}"
        )

        self.show_devices()

    # =====================================================
    # CONNECTED DEVICES
    # =====================================================

    def show_devices(self):

        self.clear_content()

        title = tk.Label(
            self.content_frame,
            text="Connected Devices",
            font=("Arial", 23, "bold"),
            bg=self.background_color
        )

        title.pack(
            pady=20
        )

        details = self.get_current_network()

        if not details:
            return

        new_network = details["network"]

        # Detect network change
        if (
            self.current_network is not None
            and self.current_network != new_network
        ):

            self.current_devices = []

        self.current_network = new_network

        # -----------------------------
        # CURRENT NETWORK LABEL
        # -----------------------------

        network_label = tk.Label(
            self.content_frame,
            text=f"Current Network: {self.current_network}",
            font=("Arial", 11, "bold"),
            bg=self.background_color
        )

        network_label.pack(
            pady=5
        )

        # -----------------------------
        # BUTTON
        # -----------------------------

        tk.Button(
            self.content_frame,
            text="Refresh Current Network",
            width=25,
            command=self.scan_current_network
        ).pack(
            pady=10
        )

        # -----------------------------
        # TABLE
        # -----------------------------

        columns = (
            "name",
            "ip",
            "mac",
            "status"
        )

        self.device_table = ttk.Treeview(
            self.content_frame,
            columns=columns,
            show="headings"
        )

        self.device_table.heading(
            "name",
            text="Device Name"
        )

        self.device_table.heading(
            "ip",
            text="IP Address"
        )

        self.device_table.heading(
            "mac",
            text="MAC Address"
        )

        self.device_table.heading(
            "status",
            text="Status"
        )

        self.device_table.column(
            "name",
            width=220
        )

        self.device_table.column(
            "ip",
            width=160
        )

        self.device_table.column(
            "mac",
            width=190
        )

        self.device_table.column(
            "status",
            width=120
        )

        self.device_table.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=15
        )

        # -----------------------------
        # SHOW ONLY CURRENT DEVICES
        # -----------------------------

        for device in self.current_devices:

            self.device_table.insert(
                "",
                "end",
                values=(
                    device["name"],
                    device["ip"],
                    device["mac"],
                    "ONLINE"
                )
            )

        if not self.current_devices:

            tk.Label(
                self.content_frame,
                text=(
                    "No current devices loaded.\n\n"
                    "Click 'Refresh Current Network' "
                    "to scan."
                ),
                font=("Arial", 11),
                bg=self.background_color
            ).pack(
                pady=15
            )

    # =====================================================
    # DEVICE DETAILS
    # =====================================================

    def show_device_details(self):

        self.clear_content()

        title = tk.Label(
            self.content_frame,
            text="Device Details",
            font=("Arial", 22, "bold"),
            bg=self.background_color
        )

        title.pack(
            pady=20
        )

        devices = get_saved_devices()

        columns = (
            "id",
            "name",
            "ip",
            "mac",
            "first_seen",
            "last_seen",
            "status",
            "network"
        )

        table = ttk.Treeview(
            self.content_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "name": "Device",
            "ip": "IP Address",
            "mac": "MAC Address",
            "first_seen": "First Seen",
            "last_seen": "Last Seen",
            "status": "Status",
            "network": "Network"
        }

        for column in columns:

            table.heading(
                column,
                text=headings[column]
            )

        for device in devices:

            table.insert(
                "",
                "end",
                values=device
            )

        table.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

    # =====================================================
    # DEVICE HISTORY
    # =====================================================

    def show_device_history(self):

        self.clear_content()

        title = tk.Label(
            self.content_frame,
            text="Device History",
            font=("Arial", 22, "bold"),
            bg=self.background_color
        )

        title.pack(
            pady=20
        )

        devices = get_saved_devices()

        columns = (
            "name",
            "ip",
            "mac",
            "first_seen",
            "last_seen",
            "status",
            "network"
        )

        table = ttk.Treeview(
            self.content_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "name": "Device",
            "ip": "IP Address",
            "mac": "MAC Address",
            "first_seen": "First Seen",
            "last_seen": "Last Seen",
            "status": "Status",
            "network": "Network"
        }

        for column in columns:

            table.heading(
                column,
                text=headings[column]
            )

        for device in devices:

            table.insert(
                "",
                "end",
                values=(
                    device[1],
                    device[2],
                    device[3],
                    device[4],
                    device[5],
                    device[6],
                    device[7]
                )
            )

        table.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

    # =====================================================
    # EVENT HISTORY
    # =====================================================

    def show_event_history(self):

        self.clear_content()

        title = tk.Label(
            self.content_frame,
            text="Event History",
            font=("Arial", 22, "bold"),
            bg=self.background_color
        )

        title.pack(
            pady=20
        )

        events = get_events()

        columns = (
            "id",
            "name",
            "ip",
            "mac",
            "event",
            "time",
            "network"
        )

        table = ttk.Treeview(
            self.content_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "name": "Device",
            "ip": "IP Address",
            "mac": "MAC Address",
            "event": "Event",
            "time": "Time",
            "network": "Network"
        }

        for column in columns:

            table.heading(
                column,
                text=headings[column]
            )

        for event in events:

            table.insert(
                "",
                "end",
                values=event
            )

        table.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

    # =====================================================
    # NETWORK SCAN
    # =====================================================

    def show_network_scan(self):

        self.clear_content()

        title = tk.Label(
            self.content_frame,
            text="Network Scan",
            font=("Arial", 22, "bold"),
            bg=self.background_color
        )

        title.pack(
            pady=20
        )

        details = self.get_current_network()

        if details:

            self.current_network = details["network"]

            tk.Label(
                self.content_frame,
                text=(
                    f"Current Network: "
                    f"{self.current_network}"
                ),
                font=("Arial", 11, "bold"),
                bg=self.background_color
            ).pack(
                pady=10
            )

        tk.Button(
            self.content_frame,
            text="Scan Current Network",
            width=25,
            command=self.scan_current_network
        ).pack(
            pady=20
        )

    # =====================================================
    # MONITORING PAGE
    # =====================================================

    def show_monitoring(self):

        self.clear_content()

        title = tk.Label(
            self.content_frame,
            text="Network Monitoring",
            font=("Arial", 22, "bold"),
            bg=self.background_color
        )

        title.pack(
            pady=20
        )

        # -----------------------------
        # BUTTONS
        # -----------------------------

        button_frame = tk.Frame(
            self.content_frame,
            bg=self.background_color
        )

        button_frame.pack(
            pady=10
        )

        tk.Button(
            button_frame,
            text="Start Monitoring",
            width=20,
            command=self.start_monitoring
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Stop Monitoring",
            width=20,
            command=self.stop_monitoring
        ).pack(
            side="left",
            padx=5
        )

        # -----------------------------
        # MONITOR STATUS
        # -----------------------------

        status = (
            "RUNNING"
            if self.monitor.running
            else "STOPPED"
        )

        self.monitor_status_label = tk.Label(
            self.content_frame,
            text=f"Monitoring Status: {status}",
            font=("Arial", 11, "bold"),
            bg=self.background_color
        )

        self.monitor_status_label.pack(
            pady=10
        )

        # -----------------------------
        # MONITOR LOG
        # -----------------------------

        self.monitor_text = tk.Text(
            self.content_frame,
            height=15,
            bg=self.background_color,
            fg=self.text_color,
        )

        self.monitor_text.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=20
        )

        self.monitor_text.insert(
            "end",
            "Network monitoring log\n"
            "=======================\n"
        )

        if self.monitor.running:

            self.monitor_text.insert(
                "end",
                "Monitoring is currently running.\n"
            )

        else:

            self.monitor_text.insert(
                "end",
                "Monitoring is currently stopped.\n"
            )

    # =====================================================
    # START MONITORING
    # =====================================================

    def start_monitoring(self):

        if self.monitor.running:

            messagebox.showinfo(
                "Monitoring",
                "Monitoring is already running."
            )

            return

        self.monitor.start()

        if self.monitor_status_label:

            self.monitor_status_label.config(
                text="Monitoring Status: RUNNING"
            )

        if self.monitor_text:

            self.monitor_text.insert(
                "end",
                "Monitoring started.\n"
            )

    # =====================================================
    # STOP MONITORING
    # =====================================================

    def stop_monitoring(self):

        self.monitor.stop()

        if hasattr(
            self,
            "monitor_status_label"
        ):

            try:

                self.monitor_status_label.config(
                    text="Monitoring Status: STOPPED"
                )

            except Exception:
                pass

        if self.monitor_text:

            self.monitor_text.insert(
                "end",
                "Monitoring stopped.\n"
            )

    # =====================================================
    # MONITOR MESSAGE
    # =====================================================

    def monitor_message(self, message):

        self.root.after(
            0,
            self._display_monitor_message,
            message
        )

    # =====================================================
    # DISPLAY MONITOR MESSAGE
    # =====================================================

    def _display_monitor_message(self, message):

        if self.monitor_text:

            try:

                self.monitor_text.insert(
                    "end",
                    f"{message}\n"
                )

                self.monitor_text.see(
                    "end"
                )

            except Exception:
                pass

        # ---------------------------------------------
        # NETWORK CHANGE DETECTED
        # ---------------------------------------------

        if "New network:" in message:

            try:

                new_network = message.split(
                    "New network:",
                    1
                )[1].strip()

                self.current_network = new_network

                # Clear old current devices
                self.current_devices = []

                if self.monitor_text:

                    self.monitor_text.insert(
                        "end",
                        "\n"
                        "CURRENT DEVICE LIST CLEARED\n"
                        "Waiting for new network scan...\n\n"
                    )

                # Refresh after network change
                self.root.after(
                    1500,
                    self.refresh_current_devices
                )

            except Exception:
                pass

    # =====================================================
    # REFRESH CURRENT DEVICES
    # =====================================================

    def refresh_current_devices(self):

        try:

            details = self.get_current_network()

            if not details:
                return

            self.current_network = details["network"]

            devices = scan_network(
                self.current_network
            )

            self.current_devices = devices

            current_time = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # Save devices with current network
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

            # Refresh connected devices page
            self.show_devices()

        except Exception as error:

            if self.monitor_text:

                try:

                    self.monitor_text.insert(
                        "end",
                        f"Refresh error: {error}\n"
                    )

                except Exception:
                    pass

    # =====================================================
    # EXIT
    # =====================================================

    def exit_application(self):

        self.monitor.stop()

        self.root.destroy()


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = WifiManagerGUI(
        root
    )

    root.mainloop()