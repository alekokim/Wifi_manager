import requests
from .base_router import BaseRouter


class TendaRouter(BaseRouter):

    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()

    def login(self):
        print(f"Connecting to Tenda router at {self.base_url}...")
        return True

    def get_devices(self):
        url = (
            f"{self.base_url}/goform/getStatus"
            "?modules=internetStatus%2CwifiRelay"
        )

        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        print("\nRouter status received.")

        online_number = data.get(
            "deviceStatistics", {}
        ).get(
            "statusOnlineNumber", "0"
        )

        print(f"Online devices reported by router: {online_number}")

        return data

    def get_status(self):
        return {}