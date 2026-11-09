import subprocess


def get_wifi_profiles():

    try:

        result = subprocess.run(
            [
                "netsh",
                "wlan",
                "show",
                "profiles"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        profiles = []

        for line in result.stdout.splitlines():

            if "All User Profile" in line:

                profile = line.split(":", 1)[1].strip()

                profiles.append(profile)

        return profiles

    except Exception as error:

        print(f"Unable to get Wi-Fi profiles: {error}")

        return []


def connect_to_wifi(network_name):

    print(
        f"\nAttempting to connect to: {network_name}"
    )

    try:

        result = subprocess.run(
            [
                "netsh",
                "wlan",
                "connect",
                f"name={network_name}"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        print(result.stdout.strip())

        if result.returncode == 0:

            print(
                f"\nConnection command sent for "
                f"'{network_name}'."
            )

            return True

        print("\nWindows could not connect.")

        if result.stderr:

            print(result.stderr.strip())

        return False

    except Exception as error:

        print(
            f"\nConnection error: {error}"
        )

        return False


def show_wifi_profiles():

    profiles = get_wifi_profiles()

    if not profiles:

        print(
            "\nNo saved Wi-Fi profiles were found."
        )

        return

    print("\n===== SAVED WINDOWS WI-FI PROFILES =====")

    for number, profile in enumerate(
        profiles,
        start=1
    ):

        print(
            f"{number}. {profile}"
        )