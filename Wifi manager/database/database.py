import sqlite3

DATABASE_NAME = "wifi_manager.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    return sqlite3.connect(
        DATABASE_NAME
    )


# =========================================================
# CHECK WHETHER COLUMN EXISTS
# =========================================================

def column_exists(
    cursor,
    table_name,
    column_name
):

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    for column in columns:

        if column[1] == column_name:
            return True

    return False


# =========================================================
# CREATE / UPDATE DATABASE
# =========================================================

def create_database():

    connection = get_connection()

    cursor = connection.cursor()

    # =====================================================
    # NETWORKS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            router_type TEXT NOT NULL,
            router_url TEXT NOT NULL,
            username TEXT,
            password TEXT
        )
    """)

    # =====================================================
    # DEVICES TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT,
            ip_address TEXT NOT NULL,
            mac_address TEXT NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # =====================================================
    # ADD NETWORK COLUMN IF IT DOES NOT EXIST
    # =====================================================

    if not column_exists(
        cursor,
        "devices",
        "network"
    ):

        cursor.execute("""
            ALTER TABLE devices
            ADD COLUMN network TEXT
        """)

        print(
            "Added 'network' column to devices table."
        )

    # =====================================================
    # EVENTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT,
            ip_address TEXT,
            mac_address TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_time TEXT NOT NULL
        )
    """)

    # =====================================================
    # ADD NETWORK COLUMN TO EVENTS
    # =====================================================

    if not column_exists(
        cursor,
        "events",
        "network"
    ):

        cursor.execute("""
            ALTER TABLE events
            ADD COLUMN network TEXT
        """)

        print(
            "Added 'network' column to events table."
        )

    connection.commit()

    connection.close()


# =========================================================
# NETWORK FUNCTIONS
# =========================================================

def add_network(
    name,
    router_type,
    router_url,
    username,
    password
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO networks
        (
            name,
            router_type,
            router_url,
            username,
            password
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        router_type,
        router_url,
        username,
        password
    ))

    connection.commit()

    connection.close()


def get_networks():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM networks"
    )

    networks = cursor.fetchall()

    connection.close()

    return networks


def get_network_by_id(network_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM networks
        WHERE id = ?
    """, (network_id,))

    network = cursor.fetchone()

    connection.close()

    return network


def delete_network(network_id):
    """Delete a saved network configuration by its database ID."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM networks WHERE id = ?",
        (network_id,),
    )

    deleted = cursor.rowcount > 0
    connection.commit()
    connection.close()

    return deleted


# =========================================================
# DEVICE FUNCTIONS
# =========================================================

def save_device(
    device_name,
    ip_address,
    mac_address,
    first_seen,
    last_seen,
    status,
    network=None
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM devices
        WHERE mac_address = ?
        AND network = ?
    """, (
        mac_address,
        network
    ))

    existing_device = cursor.fetchone()

    if existing_device:

        cursor.execute("""
            UPDATE devices
            SET
                device_name = ?,
                ip_address = ?,
                last_seen = ?,
                status = ?
            WHERE mac_address = ?
            AND network = ?
        """, (
            device_name,
            ip_address,
            last_seen,
            status,
            mac_address,
            network
        ))

    else:

        cursor.execute("""
            INSERT INTO devices
            (
                device_name,
                ip_address,
                mac_address,
                first_seen,
                last_seen,
                status,
                network
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            device_name,
            ip_address,
            mac_address,
            first_seen,
            last_seen,
            status,
            network
        ))

    connection.commit()

    connection.close()


def update_device_status(
    mac_address,
    status,
    network=None
):

    connection = get_connection()

    cursor = connection.cursor()

    if network is not None:

        cursor.execute("""
            UPDATE devices
            SET status = ?
            WHERE mac_address = ?
            AND network = ?
        """, (
            status,
            mac_address,
            network
        ))

    else:

        cursor.execute("""
            UPDATE devices
            SET status = ?
            WHERE mac_address = ?
        """, (
            status,
            mac_address
        ))

    connection.commit()

    connection.close()


def get_saved_devices():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            device_name,
            ip_address,
            mac_address,
            first_seen,
            last_seen,
            status,
            network
        FROM devices
        ORDER BY last_seen DESC
    """)

    devices = cursor.fetchall()

    connection.close()

    return devices


def get_devices_by_network(network):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            device_name,
            ip_address,
            mac_address,
            first_seen,
            last_seen,
            status,
            network
        FROM devices
        WHERE network = ?
        ORDER BY last_seen DESC
    """, (network,))

    devices = cursor.fetchall()

    connection.close()

    return devices


def get_device_by_id(device_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            device_name,
            ip_address,
            mac_address,
            first_seen,
            last_seen,
            status,
            network
        FROM devices
        WHERE id = ?
    """, (device_id,))

    device = cursor.fetchone()

    connection.close()

    return device


# =========================================================
# EVENT FUNCTIONS
# =========================================================

def add_event(
    device_name,
    ip_address,
    mac_address,
    event_type,
    event_time,
    network=None
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO events
        (
            device_name,
            ip_address,
            mac_address,
            event_type,
            event_time,
            network
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        device_name,
        ip_address,
        mac_address,
        event_type,
        event_time,
        network
    ))

    connection.commit()

    connection.close()


def get_events():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            device_name,
            ip_address,
            mac_address,
            event_type,
            event_time,
            network
        FROM events
        ORDER BY id DESC
    """)

    events = cursor.fetchall()

    connection.close()

    return events


def get_events_by_network(network):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            device_name,
            ip_address,
            mac_address,
            event_type,
            event_time,
            network
        FROM events
        WHERE network = ?
        ORDER BY id DESC
    """, (network,))

    events = cursor.fetchall()

    connection.close()

    return events


# =========================================================
# TEST DATABASE
# =========================================================

if __name__ == "__main__":

    create_database()

    print()
    print("Database is ready.")
    print("Network-aware database structure is active.")