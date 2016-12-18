import json
import logging
import os
import os.path
import requests

logger = logging.getLogger('onedrive')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

base_url = 'https://api.onedrive.com/v1.0'


def exists(file, auth):
    code = requests.get(base_url + "/drive/root:" + file, headers=auth).status_code
    return code == 200


def get_metadata(file, auth):
    """ https://dev.onedrive.com/items/get.htm """
    r = requests.get(base_url+"/drive/root:" + file, headers=auth)
    return json.loads(r.text)


def mkdir(parent, new_dir, auth):
    # check if dir exists
    meta_target = get_metadata(file=parent + new_dir, auth=auth)
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
    meta_parent = get_metadata(file=parent, auth=auth)
    r = requests.post(base_url+"/drive/items/"+meta_parent["id"]+"/children", headers=headers, data=data)
    response = json.loads(r.text)
    if r.status_code != 201 or response.get('id') is None:
        logger.error(json.dumps(response, sort_keys=True))
        return False
    else:
        logger.info("created "+parent+new_dir)
        return True


def mkdirs(file, auth):
    """Ensure file path exists. Elements with dots are removed.
    TODO: Could/Should be more elaborate.
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
        success = mkdir(parent=path, new_dir=dir, auth=auth)
        if not success:
            return False
        path += dir

    return True


def delete(file, auth):
    r = requests.delete(base_url+"/drive/root:"+file, headers = auth)
    if r.status_code == 204:
        return True
    else:
        logger.error("delete failed: ", r.status_code)
        return False


def get_sha1(file, auth):
    m = get_metadata(file, auth)
    return m.get('file', {}).get('hashes', {}).get('sha1Hash')


def copy(src, dst, auth):
    """Copy a onedrive file. creates target parent directories, replaces target if hashes do not equal
    TODO improve return type!!!
    :param src:
    :param dst:
    :param auth:
    :return: URL for a AsyncJobStatus or the final URL or None if an error occurs
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

    dst_meta = get_metadata(file=dst, auth=auth)
    src_meta = get_metadata(file=src, auth=auth)
    if dst_meta.get('id') is not None:  # target exists
        if dst_meta.get('file') is None:  # target is not a file
            logger.info("target not a file: deleting \n ", json.dumps(dst_meta, sort_keys=True, indent=4))
            delete(file=dst, auth=auth)
        else:                             # destination exists and is a file
            if src_meta['file']['hashes']['sha1Hash'] == dst_meta['file']['hashes']['sha1Hash']:  # equal Hashes
                logger.info("target with same hash: returning")
                return dst
            else:  # hashes are unequal: replace target
                logger.info("target with different hash: deleting")
                delete(file=dst, auth=auth)

    logger.info("ensure parent dirs")
    mkdirs(file=dst, auth=auth)

    logger.info("copying file")
    copy_request = requests.post(base_url+'/drive/root:'+src+':/action.copy', headers=header, data=data)
    if copy_request.status_code != 202:
        response = json.loads(copy_request.text)
        logger.error(json.dumps(response, sort_keys=True))
        return None
    else:
        logger.info("file copy in progress")
        return copy_request.headers['Location']
