import json
from os import path


def save(tokens, file):
    with open(file, 'w') as f:
        json.dump(tokens, f)
    f.close()


def load(file):
    if not path.exists(file):
        raise IOError("app keys need to be set - see onedrive_keys.json.sample")

    with open(file, 'r') as f:
        tokens = json.load(f)
    f.close()
    return tokens


