FEATURE_FLAGS = {
    "new_checkout": True,
    "dark_mode": True,
}


def checkout_path():
    return "new" if FEATURE_FLAGS["new_checkout"] else "legacy"
