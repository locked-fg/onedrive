import hashlib
import os
import os.path
import logging

logger = logging.getLogger('onedrive-simple')

def sha1_file(fname):
    """
    computes the SHA1 hash of a given file
    :param fname: filename
    :return: sha1 hash in lower chars
    """
    if not os.path.exists(fname):
        logger.error("not found: " + fname)
        raise IOError("file ", fname, " not found")

    hash_sha1 = hashlib.sha1()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha1.update(chunk)
    return hash_sha1.hexdigest().lower()
