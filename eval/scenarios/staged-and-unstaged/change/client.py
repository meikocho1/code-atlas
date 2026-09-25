from config import SETTINGS


def fetch(url):
    attempts = 0
    while attempts < SETTINGS["retry_limit"]:
        attempts += 1
        response = _request(url)
        if response["ok"]:
            return response
    return None


def _request(url):
    return {"url": url, "timeout": SETTINGS["timeout_seconds"], "ok": True}
