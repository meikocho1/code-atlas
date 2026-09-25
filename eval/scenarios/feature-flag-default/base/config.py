FEATURE_FLAGS = {
    "new_checkout": False,
    "dark_mode": True,
}


def checkout_path():
    return "new" if FEATURE_FLAGS["new_checkout"] else "legacy"
