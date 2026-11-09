# Wi-Fi Manager web app

The web interface runs on the Windows computer that is connected to the Wi-Fi network being managed. A phone or another computer on that same network can open the dashboard in its browser. The server binds to the computer's active local IP, not to all network interfaces.

## Install and start

From the project folder in PowerShell, install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

For packet-based Wi-Fi scans, install Npcap on Windows. If scans report permission or adapter errors, start PowerShell as Administrator and run the server from there.

Set a unique dashboard username, a password of at least 12 characters, and a persistent random Flask session key. Keep these values private; do not put them in source control or share the session key.

```powershell
$env:WEBAPP_USERNAME = "your-user-name"
$securePassword = Read-Host "Choose a strong dashboard password" -AsSecureString
$passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $env:WEBAPP_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
}
$env:WEBAPP_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python web_app.py
```

Keep the same `WEBAPP_SECRET_KEY` between server restarts if you want browser sessions to remain valid. For this PowerShell window, the generated value remains set until the window closes; to persist it safely between sessions, use a private environment-variable manager rather than committing it to the project.

The server prints its local address, for example `http://192.168.1.25:8000`. Open that address on your phone while it is connected to the same Wi-Fi. If Windows Firewall asks, allow Python on **Private networks only**. The computer must remain powered on and connected for the dashboard to work. Use `Ctrl+C` in the server window to stop it.

`WEBAPP_PORT` can optionally be set to another port (default `8000`). The scanner still only scans the Windows computer's currently connected subnet.

## Safety

This app can scan the local network. It requires a login and protects form actions against CSRF, but its built-in Waitress server uses plain HTTP by default. Use it only on a trusted private Wi-Fi network; anyone with network access can reach the login page, and HTTP does not encrypt credentials or session cookies. Do not configure router port forwarding or expose this service directly to the internet. For access away from home, use a VPN into the private network; for untrusted networks, put it behind HTTPS with a trusted certificate.

The live connected-device list is kept in memory and clears when the server restarts. Device history and events use the existing SQLite database.
