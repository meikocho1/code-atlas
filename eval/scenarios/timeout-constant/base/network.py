DEFAULT_TIMEOUT_SECONDS = 30


def request_timeout(override=None):
    return override if override is not None else DEFAULT_TIMEOUT_SECONDS
