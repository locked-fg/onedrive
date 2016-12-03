import json
import logging
import os
import os.path

import requests

logger = logging.getLogger('my_onedrive')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

base_url = 'https://api.my_onedrive.com/v1.0'


def onedrive_get_metadata(file, auth):
    r = requests.get(base_url+"/drive/root:" + file, headers=auth)
    return json.loads(r.text)


def onedrive_mkdir(parent, new_dir, auth):
    # check if dir exists
    meta_target = onedrive_get_metadata(file=parent+new_dir, auth=auth)
    if meta_target.get('folder') is not None:
        logger.info("folder exists: " + parent+new_dir)
        return True

    headers = dict(auth)
    headers['Content-Type'] = 'application/json'
    data = json.dumps({
        "name": new_dir.replace("/", ""),
        "folder": {}
    })

    # make dir. This somehow only works with the ID. So get the ID before.
    meta_parent = onedrive_get_metadata(file=parent, auth=auth)
    r = requests.post(base_url+"/drive/items/"+meta_parent["id"]+"/children", headers=headers, data=data)
    response = json.loads(r.text)
    if r.status_code != 201 or response.get('id') is None:
        logger.error(json.dumps(response, sort_keys=True))
        return False
    else:
        logger.info("created "+parent+new_dir)
        return True


def onedrive_mkdirs(file, auth):
    """
    Ensure file path exist. elements with dots are removed.
    Could be more elaborate.
    :param file: the file path to be created
    :param auth: the auth header
    :return: true if directories are there, false otherwise
    """
    parts = file.split("/")

    # remove first slash and file names (assuming, directories do not contain dots)
    parts = [e for e in parts if (e != "" and "." not in e)]

    path = ""
    for dir in parts:
        dir = "/" + dir
        success = onedrive_mkdir(parent=path, new_dir=dir, auth=auth)
        if not success:
            return False
        path += dir

    return True


def onedrive_delete(file, auth):
    r = requests.delete(base_url+"/drive/root:"+file, headers = auth)
    if r.status_code == 204:
        return True
    else:
        logger.error("delete failed: ", r.status_code)
        return False


def onedrive_copy(src, dst, auth):
    """
    Copy a my_onedrive file. If the destination path exists:
    - same hash: skip and return success
    - diff hash: replace destination
    :param src:
    :param dst:
    :param auth:
    :return: URL for a AsyncJobStatus or the final URL
    """
    header = dict(auth)
    header['Content-Type'] = 'application/json'
    header['Prefer'] = 'respond-async'

    dst_path, dst_file = os.path.split(dst)
    data = json.dumps({
      "parentReference": {
        "path": "/drive/root:" + dst_path
      },
      "name": dst_file
    })

    # target exists?
    dst_meta = onedrive_get_metadata(file=dst, auth=auth)
    src_meta = onedrive_get_metadata(file=src, auth=auth)
    if dst_meta.get('id') is not None:  # target exists!
        if dst_meta.get('file') is None:
            logger.info("target not a file: deleting \n ", json.dumps(dst_meta, sort_keys=True, indent=4))
            onedrive_delete(file=dst, auth=auth)
        else:
            # compare hashes
            if src_meta['file']['hashes']['sha1Hash'] == dst_meta['file']['hashes']['sha1Hash']:  # equal
                logger.info("target file already there (same hash): ignoring")
                return dst
            else:  # hashes are unequal: replace target
                logger.info("target file already there (different hash): deleting")
                onedrive_delete(file=dst, auth=auth)

    logger.info("copying file")
    copy_request = requests.post(base_url+'/drive/root:'+src+':/action.copy', headers=header, data=data)
    if copy_request.status_code != 202:
        response = json.loads(copy_request.text)
        logger.error(json.dumps(response, sort_keys=True))
        return None
    else:
        logger.info("file copy in progress")
        return copy_request.headers['Location']


def onedrive_copy_if_same_hash(auth_header, src, dst, sha1_local):
    """
    copy my_onedrive to dst if crc is same as local.
    also creates intermediate folders

    :param auth_header: auth header to authorize request
    :param src:  the source base path: '/Backup/last/DigiCam/foo.7z'
    :param dst:  the destination base path: '/Backup/new/DigiCam/foo.7z'
    :param sha1_local: the local crc hash
    :return: monitor URL if copying was triggered or None if no copy was triggered
    """
    # my_onedrive file exists?
    logger.info("checking if source file exists")
    meta_src = onedrive_get_metadata(file=src, auth=auth_header)
    if not meta_src['file']:
        logger.info("source does not exist: " + src)
        return None

    # copy only if hashes of local and source files are the same
    logger.info("comparing hashes")
    sha1_remote = meta_src['file']['hashes']['sha1Hash'].lower()
    if sha1_local != sha1_remote:
        logger.info("hashes are different for " + src)
        return None

    logger.info("Creating destination directories")
    dirs_exist = onedrive_mkdirs(file=dst, auth=auth_header)
    if not dirs_exist:
        logger.info("unable to create destination path")
        return None

    monitor = onedrive_copy(src, dst, auth_header)
    return monitor
