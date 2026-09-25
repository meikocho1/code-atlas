from config import SETTINGS


def fetch(url):
    return _request(url)


def _request(url):
    return {"url": url, "timeout": SETTINGS["timeout_seconds"]}
