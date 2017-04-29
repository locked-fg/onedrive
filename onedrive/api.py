import json
import os
import os.path
import requests
import time

base_url = 'https://api.onedrive.com/v1.0'


def exists(file, auth):
    code = requests.get(base_url + "/drive/root:" + file, headers=auth).status_code
    return code == 200


def get_metadata(file, auth, select=None):
    """
    get the metadata for the given path: https://dev.onedrive.com/items/get.htm
    https://dev.onedrive.com/odata/optional-query-parameters.htm
    :param file:
    :param auth:
    :param select: select only these properties or None for all
    :return: :rtype: Result with code 200 + json if all is okay
    """
    if select:
        q = "?select=" + select
    else:
        q = ""
    res = requests.get(base_url + "/drive/root:" + file + q, headers=auth)
    return Result(res)


def mkdir(new_dir, auth, parents=False):
    """
    creates the directory structure (compare mkdir)
    https://dev.onedrive.com/items/create.htm
    :param new_dir:
    :param auth:
    :param parents: true if parents should be created (cmp: mkdir -p)
    :return: Result with code 201 + json if dir created
    """
    dirname = os.path.basename(new_dir)
    headers = dict(auth)
    headers['Content-Type'] = 'application/json'
    data = json.dumps({
        "name": dirname,
        "folder": {}
    })

    # make dir. This somehow only works with the ID. So get the ID before.
    parent = os.path.dirname(new_dir)
    parent_meta = get_metadata(file=parent, auth=auth)

    if parent_meta.status_code == 404 and parents:  # parent does not exist but should be created!
        mkdir(parent, auth, True)  # recurse into parents
        parent_meta = get_metadata(file=parent, auth=auth)

    parent_id = dict(parent_meta.json_body()).get('id', '00000000')
    res = requests.post(base_url + "/drive/items/" + parent_id + "/children", headers=headers, data=data)
    return Result(res)


def delete(file, auth):
    """
    Deletes file.
    :param file:
    :param auth:
    :return:  204 No Content
    """
    return Result(requests.delete(base_url + "/drive/root:" + file, headers=auth))


def get_sha1(file, auth):
    """
    return the sha1 or None
    :param file: file to check
    :param auth:
    :return: the sha1 string (in UPPER cases) or None
    """
    m = get_metadata(file, auth, select='file').json_body()
    return m.get('file', {}).get('hashes', {}).get('sha1Hash', None)


def is_file_meta(meta):
    return 'file' in meta


def is_dir_meta(meta):
    return 'folder' in meta


def copy(src, dst, auth):
    """Copy a onedrive file
    https://dev.onedrive.com/items/copy.htm
    :param src:
    :param dst:
    :param auth:
    :return: URL for a AsyncJobStatus in LOCATION header with code 202
    """
    header = dict(auth)
    header['Content-Type'] = 'application/json'
    header['Prefer'] = 'respond-async'

    dst_path, dst_file = os.path.split(dst)
    if dst_path == "/":
        dst_path = ""

    data = json.dumps({
        "parentReference": {
            "path": "/drive/root:" + dst_path
        },
        "name": dst_file
    })

    copy_request = requests.post(base_url + '/drive/root:' + src + ':/action.copy', headers=header, data=data)
    return Result(copy_request)


def upload_simple(data, dst, auth, conflict='replace'):
    """ Simple item upload is available for items with less than 100MB of content.
    see: https://dev.onedrive.com/items/upload.htm
    :param data: binary stream of data
    :param dst: upload path
    :param auth: auth header
    :param conflict: fail, replace, or rename. The default for PUT is replace
    :return: 201 Created (ok, conflict=renamed), 200 Ok (conflict=replaced), 409 (conflict=fail)
    """
    url = base_url + "/drive/root:" + dst + ":/content?@name.conflictBehavior=" + conflict
    requ = requests.put(url, data=data, headers=auth)
    return Result(requ)


def download(path, auth):
    """ download a File Facet. No range downloads yet
    See: https://dev.onedrive.com/items/download.htm
    :param path: download this
    :param auth: auth header
    :return: 200 with file, maybe also 302 Found + Location with the download URL which does NOT req. authentication
    """
    url = base_url + "/drive/root:" + path + ":/content"
    requ = requests.get(url, headers=auth)
    return Result(requ)


def move(src, dst, auth):
    """move a file: https://dev.onedrive.com/items/move.htm
     :param src: the file to move. /foo/bar.tgz
     :param dst: the target directory. /bar
     :return: 200, As with other PATCH actions, the entire item object will be included in the response.
    """
    header = dict(auth)
    header['Content-Type'] = 'application/json'

    # When moving items to the root of a OneDrive you cannot use the
    # "id:" "root" syntax. You either need to use the real ID of the root folder,
    # or use {"path": "/drive/root"} for the parent reference.
    if dst == "/":
        dst_path = "/drive/root"
    else:
        dst_path = "/drive/root:" + dst
    data = json.dumps({
        "parentReference": {
            "path": dst_path
        }
    })
    res = requests.patch(base_url + '/drive/root:' + src, headers=header, data=data)
    return Result(res)


def rename(src, dst, auth):
    """
    renames a file/directory
    :param src: full path
    :param dst: new name (basename only! file/dir stays in the same dir!)
    :param auth:
    :return: 200 OK
    """
    header = dict(auth)
    header['Content-Type'] = 'application/json'

    # When moving items to the root of a OneDrive you cannot use the
    # "id:" "root" syntax. You either need to use the real ID of the root folder,
    # or use {"path": "/drive/root"} for the parent reference.
    data = json.dumps({"name": dst})
    res = requests.patch(base_url + '/drive/root:' + src, headers=header, data=data)
    return Result(res)


class Result:
    def __init__(self, response):
        self.status_code = response.status_code
        self.text = response.text
        self.headers = response.headers

    def json_body(self):
        from json import JSONDecodeError
        try:
            return json.loads(self.text)
        except JSONDecodeError:
            return self.text

    def to_string(self):
        str_header = "\n\t".join([str(k) + ":" + str(v) for k, v in self.headers.items()])
        return """
status_code: {code},
headers:
    {headers}
text: {text}""".format(code=self.status_code,
                       headers=str_header,
                       text=json.dumps(self.json_body(), indent=2))


class AsyncOperationStatus:
    """https://dev.onedrive.com/resources/asyncJobStatus.htm"""
    refresh_delay = 0.5

    def __init__(self, location, auth):
        self.location = location
        self.auth = auth

        self.operation = None
        self.status = None
        self.response = None  # the final response
        self.percentageComplete = 0.0

        self.refresh()

    def refresh(self):
        req = requests.get(self.location, headers=self.auth)
        if req.history:  # it is the redirected response already
            self.operation = None
            self.percentageComplete = 100
            self.status = 'completed'
            self.response = req
        else:
            data = json.loads(req.text)
            self.operation = data.get('operation', None)
            self.percentageComplete = data.get('percentageComplete', 0.0)
            self.status = data.get('status', None)

    def operation(self):
        return self.operation

    def complete(self):
        return self.percentageComplete

    def status(self):
        """
        :return:  notStarted | inProgress | completed | updating | failed | deletePending | deleteFailed | waiting
        """
        return self.status

    def response(self):
        return self.response

    def block(self):
        while self.percentageComplete < 100:
            time.sleep(AsyncOperationStatus.refresh_delay)  # wait this many sec
            self.refresh()
