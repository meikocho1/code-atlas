DEFAULT_TIMEOUT_SECONDS = 60


def request_timeout(override=None):
    return override if override is not None else DEFAULT_TIMEOUT_SECONDS
