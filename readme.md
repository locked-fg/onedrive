# Simple Microsoft OneDrive Python API

This is a more basic version of the official [OneDrive-Python-API](https://github.com/OneDrive/onedrive-sdk-python). This project is intended to abstract login etc and 
make interaction with OneDrive as easy as possible.
This library uses the REST endpoints as documented in the [OneDrive API Docs](https://dev.onedrive.com/README.htm). 

The library was built with Python3 for pure personal use. So downwards compatibility to Python 2 was and still is 
not (yet) subject of development.

## Install and setup
- Clone this repo
- Call ```python setup.py install``` to build and install the library 
- Acquire Api key and API through [https://apps.dev.microsoft.com](https://apps.dev.microsoft.com)
- Save Api key and secret to [onedrive_keys.json](onedrive_keys.json.sample) 

## Interact / Examples / How To
See [tests/test_api.py](tests/test_api.py) for working code. The tests should be pretty self explanatory.

### Login: 
```
from onedrive import auth
auth.login()
```
The above code launches a browser window and asks for permission to interact with your 1Drive.
According authentication tokens are saved in `tokens.json` so that you do not need to authenticate in 
each session. 

### Copy file
```
from onedrive import auth
from onedrive import api

header = auth.login()  # log in (open broeser or reuse login from tokens.json)
api.mkdir("/api_test/x", header, parents=True)  # create dir 

content = "1".encode("utf-8")
api.upload_simple(data=content, dst="/api_test/foo.tmp", auth=header)  # upload a new file 

res = api.copy("/api_test/foo.tmp", "/api_test/x/foo2.tmp", header)  # copy the file
```

### Delete File/Folder
```
from onedrive import auth
from onedrive import api
header = auth.login()
api.delete("/api_test", header)
```

### Other operations (upload, download, copy, move, get meta data)
Please have a look at [tests/test_api.py](tests/test_api.py).
All methods are documented there.

# TODO
- save URLs of long running tasks: https://dev.onedrive.com/misc/long-running-actions.htm
- list status of long running tasks
- CLI 

# Throttling
This part is copied from [OneDrive API README](https://dev.onedrive.com/README.htm):
OneDrive has limits in place to make sure that individuals and apps do not adversely affect the experience of other users. When an activity exceeds OneDrive's limits, API requests will be rejected for a period of time. OneDrive may also return a Retry-After header with the number of seconds your app should wait before sending more requests.
```
HTTP/1.1 429 Too Many Requests  
Retry-After: 3600
```

# License
The project is licensed under the [MIT License](LICENSE).