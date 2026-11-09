import hmac
import os
import secrets
import subprocess
import threading
from collections import deque
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from waitress import serve

from database.database import (
    create_database,
    get_events,
    get_saved_devices,
    save_device,
)
from monitor_service import NetworkMonitor
from network_scanner import get_network_details, scan_network


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("WEBAPP_SECRET_KEY"),
        WEBAPP_USERNAME=os.environ.get("WEBAPP_USERNAME"),
        WEBAPP_PASSWORD=os.environ.get("WEBAPP_PASSWORD"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_SECURE=os.environ.get(
            "WEBAPP_COOKIE_SECURE", ""
        ).lower() in {"1", "true", "yes"},
        PERMANENT_SESSION_LIFETIME=8 * 60 * 60,
    )
    if test_config:
        app.config.update(test_config)

    required_settings = (
        "SECRET_KEY",
        "WEBAPP_USERNAME",
        "WEBAPP_PASSWORD",
    )
    missing_settings = [
        setting
        for setting in required_settings
        if not app.config.get(setting)
    ]
    if missing_settings:
        raise RuntimeError(
            "Set these environment variables before starting the web app: "
            + ", ".join(
                {
                    "SECRET_KEY": "WEBAPP_SECRET_KEY",
                    "WEBAPP_USERNAME": "WEBAPP_USERNAME",
                    "WEBAPP_PASSWORD": "WEBAPP_PASSWORD",
                }[setting]
                for setting in missing_settings
            )
        )
    if len(app.config["WEBAPP_PASSWORD"]) < 12:
        raise RuntimeError(
            "WEBAPP_PASSWORD must be at least 12 characters long."
        )
    if len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError(
            "WEBAPP_SECRET_KEY must be at least 32 characters long."
        )

    app.extensions["scan_lock"] = threading.Lock()
    app.extensions["state_lock"] = threading.Lock()
    app.extensions["current_devices"] = []
    app.extensions["current_network"] = None
    app.extensions["monitor_logs"] = deque(maxlen=200)
    app.extensions["monitor_log_lock"] = threading.Lock()

    monitor = NetworkMonitor(interval=30)
    app.extensions["network_monitor"] = monitor

    def record_monitor_message(message):
        timestamped_message = (
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {message}"
        )
        with app.extensions["monitor_log_lock"]:
            app.extensions["monitor_logs"].append(timestamped_message)

    monitor.add_callback(record_monitor_message)

    @app.before_request
    def ensure_csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        if request.method == "POST":
            submitted_token = request.form.get("csrf_token", "")
            if not hmac.compare_digest(
                session["csrf_token"],
                submitted_token,
            ):
                abort(400, description="Invalid or missing CSRF token.")

    @app.after_request
    def set_security_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; "
            "form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        return response

    def login_required(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not session.get("authenticated"):
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)

        return wrapped_view

    def current_devices():
        with app.extensions["state_lock"]:
            return list(app.extensions["current_devices"])

    def current_network():
        with app.extensions["state_lock"]:
            return app.extensions["current_network"]

    def scan_current_network():
        with app.extensions["scan_lock"]:
            details = get_network_details()
            network = details["network"]
            devices = scan_network(network)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for device in devices:
                save_device(
                    device_name=device["name"],
                    ip_address=device["ip"],
                    mac_address=device["mac"],
                    first_seen=now,
                    last_seen=now,
                    status="ONLINE",
                    network=network,
                )

            with app.extensions["state_lock"]:
                app.extensions["current_network"] = network
                app.extensions["current_devices"] = devices

        return network, devices

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if session.get("authenticated"):
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            username_ok = hmac.compare_digest(
                request.form.get("username", ""),
                app.config["WEBAPP_USERNAME"],
            )
            password_ok = hmac.compare_digest(
                request.form.get("password", ""),
                app.config["WEBAPP_PASSWORD"],
            )
            if username_ok and password_ok:
                session.clear()
                session["authenticated"] = True
                session.permanent = True
                session["csrf_token"] = secrets.token_urlsafe(32)
                return redirect(url_for("dashboard"))
            flash("Incorrect username or password.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        flash("You have been signed out.", "success")
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def dashboard():
        details = None
        network_error = None
        try:
            details = get_network_details()
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            network_error = str(error)

        active_network = details["network"] if details else current_network()
        online_count = sum(
            1
            for device in current_devices()
            if device.get("status", "ONLINE") == "ONLINE"
        )
        return render_template(
            "dashboard.html",
            page="dashboard",
            details=details,
            network_error=network_error,
            active_network=active_network,
            online_count=online_count,
            monitor=app.extensions["network_monitor"],
        )

    @app.get("/devices")
    @login_required
    def devices():
        try:
            details = get_network_details()
            with app.extensions["state_lock"]:
                app.extensions["current_network"] = details["network"]
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            details = None
            flash(f"Could not read the active network: {error}", "error")
        return render_template(
            "devices.html",
            page="devices",
            devices=current_devices(),
            network=details["network"] if details else current_network(),
        )

    @app.get("/devices/history")
    @login_required
    def device_history():
        return render_template(
            "table.html",
            page="device-history",
            title="Device history",
            description="Previously discovered devices and their last known status.",
            headers=(
                "Device",
                "IP address",
                "MAC address",
                "First seen",
                "Last seen",
                "Status",
                "Network",
            ),
            rows=[device[1:] for device in get_saved_devices()],
            empty_message="No device history yet. Scan your local network to get started.",
        )

    @app.get("/devices/details")
    @login_required
    def device_details():
        return render_template(
            "table.html",
            page="device-details",
            title="Device details",
            description="Saved device records, including their database IDs.",
            headers=(
                "ID",
                "Device",
                "IP address",
                "MAC address",
                "First seen",
                "Last seen",
                "Status",
                "Network",
            ),
            rows=get_saved_devices(),
            empty_message="No saved devices yet.",
        )

    @app.get("/events")
    @login_required
    def events():
        return render_template(
            "table.html",
            page="events",
            title="Event history",
            description="Device connection events recorded by network monitoring.",
            headers=(
                "ID",
                "Device",
                "IP address",
                "MAC address",
                "Event",
                "Time",
                "Network",
            ),
            rows=get_events(),
            empty_message="No events recorded yet. Start monitoring to track changes.",
        )

    @app.route("/scan", methods=("GET", "POST"))
    @login_required
    def scan():
        if request.method == "POST":
            try:
                network, found_devices = scan_current_network()
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                flash(f"Network scan failed: {error}", "error")
            else:
                flash(
                    f"Found {len(found_devices)} device(s) on {network}.",
                    "success",
                )
                return redirect(url_for("devices"))

        try:
            details = get_network_details()
            network_error = None
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            details = None
            network_error = str(error)
        return render_template(
            "scan.html",
            page="scan",
            details=details,
            network_error=network_error,
        )

    @app.get("/monitor")
    @login_required
    def monitoring():
        with app.extensions["monitor_log_lock"]:
            logs = list(app.extensions["monitor_logs"])
        return render_template(
            "monitoring.html",
            page="monitoring",
            monitor=app.extensions["network_monitor"],
            logs=logs,
        )

    @app.post("/monitor/start")
    @login_required
    def start_monitoring():
        monitor.start()
        flash("Network monitoring started.", "success")
        return redirect(url_for("monitoring"))

    @app.post("/monitor/stop")
    @login_required
    def stop_monitoring():
        monitor.stop()
        flash("Network monitoring stopped.", "success")
        return redirect(url_for("monitoring"))

    return app


def main():
    create_database()
    app = create_app()
    try:
        details = get_network_details()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(f"Cannot start the LAN web app: {error}") from error

    try:
        port = int(os.environ.get("WEBAPP_PORT", "8000"))
    except ValueError as error:
        raise SystemExit("WEBAPP_PORT must be a valid port number.") from error
    if not 1 <= port <= 65535:
        raise SystemExit("WEBAPP_PORT must be between 1 and 65535.")

    print(f"Wi-Fi Manager is available at http://{details['local_ip']}:{port}")
    print("Keep this computer on the same Wi-Fi network as your phone.")
    print("Press Ctrl+C to stop the server.")
    serve(app, host=details["local_ip"], port=port)


if __name__ == "__main__":
    main()
