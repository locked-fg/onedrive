import json

def save(tokens, fname):
    with open(fname, 'w') as f:
        json.dump(tokens, f)
    f.close()


def load(fname):
    with open(fname, 'r') as f:
        tokens = json.load(f)
    f.close()
    return tokens


