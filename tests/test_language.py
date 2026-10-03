import unittest
from unittest.mock import patch

from ecohome.client import AsyncEcoHomeClient


class _Response:
    def __init__(self, data: dict):
        self._data = data
        self.cookies = {}

    def json(self) -> dict:
        return self._data

    def raise_for_status(self) -> None:
        pass


class _HttpClient:
    def __init__(self) -> None:
        self.requests: list[tuple[str, str, dict]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url: str, **kwargs) -> _Response:
        self.requests.append(("GET", url, kwargs))
        return _Response({"error_code": "0"})

    async def post(self, url: str, **kwargs) -> _Response:
        self.requests.append(("POST", url, kwargs))
        if url.endswith("/user/login.json"):
            return _Response(
                {
                    "error_code": "0",
                    "error_msg": "",
                    "object_result": {"user_id": 1, "x-token": "token"},
                }
            )
        if url.endswith("/device/deviceList.json"):
            return _Response({"error_code": "0", "object_result": []})
        if url.endswith("/deviceInfo/getDeviceBaseInfo.json"):
            return _Response({"error_code": "0", "object_result": {}})
        if url.endswith(("/deviceInfo/getDeviceDetailV3", "/deviceInfo/paramListV3")):
            return _Response({"errorCode": 200, "objectResult": []})
        return _Response({"error_code": "0"})


class LanguageTest(unittest.IsolatedAsyncioTestCase):
    async def test_all_requests_use_english(self) -> None:
        http = _HttpClient()
        with (
            patch("ecohome.client.httpx.AsyncClient", return_value=http),
            patch("ecohome.client._load_credentials", return_value={}),
            patch("ecohome.client._save_credentials"),
        ):
            client = await AsyncEcoHomeClient.login("user", "password", save_credentials=False)
            await client.is_logged_in()
            await client.list_devices()
            await client.get_device_base_info("device")
            await client.get_device_detail("device")
            await client.get_param_list("device", 0)
            await client.update_switch_state("device", "address", True)
            await client.set_value("device", "address", 20)
            await client.logout()

        self.assertGreater(len(http.requests), 0)
        for _, _, kwargs in http.requests:
            self.assertEqual(kwargs["params"], {"lang": "en_US"})
            self.assertEqual(kwargs["headers"]["Accept-Language"], "en-US,en;q=0.9")


if __name__ == "__main__":
    unittest.main()
