import requests
import urllib.parse
import webbrowser
import json
import os
import os.path
from urllib.parse import parse_qs
from urllib.parse import urlparse
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler
import onedrive


class AuthCodeHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            # Extract the code query param
            AuthCodeHandler.auth_code = params["code"][0]
        if "error" in params:
            error_msg, error_desc = (unquote(params["error"][0]),
                                     unquote(params["error_description"][0]))
            raise RuntimeError("The server returned an error: {} - {}"
                               .format(error_msg, error_desc))
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes('<script type="text/javascript">window.close()</script>'.encode("utf-8")))
        self.server.server_close()


def get_auth_code(client_id):
    redirect_uri=urllib.parse.quote('http://localhost:8080')
    scopes=urllib.parse.quote('wl.signin,wl.offline_access,onedrive.readwrite')
    url = 'https://login.live.com/oauth20_authorize.srf?client_id={client_id}&scope={scope}&response_type=code&redirect_uri={redirect_uri}'.format(
        client_id=client_id,
        scope=scopes,
        redirect_uri=redirect_uri)
    webbrowser.open(url, new=1, autoraise=True)

    httpd = HTTPServer(('localhost', 8080), AuthCodeHandler)
    try:
        httpd.serve_forever()
    except OSError:
        pass
    return AuthCodeHandler.auth_code


def get_tokens(auth_code, client_id, client_secret):
    body = "client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&code={code}&grant_type=authorization_code"\
        .format(client_id=client_id,
                redirect_uri='http://localhost:8080',
                client_secret=client_secret,
                code=auth_code)
    r = requests.post('https://login.live.com/oauth20_token.srf',
                      headers={'Content-type': 'application/x-www-form-urlencoded'},
                      data=body)
    j = json.loads(r.text)
    # print(json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')))
    # {
    #     "access_token": "EwA...oAg==",
    #     "expires_in": 3600,
    #     "refresh_token": "MC...Bvg$$",
    #     "scope": "wl.signin wl.offline_access onedrive.readwrite",
    #     "token_type": "bearer",
    #     "user_id": "AA...X30"
    # }
    return j


def refresh_tokens(refresh_token, client_id, client_secret):
    body = "client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&refresh_token={refresh_token}&grant_type=refresh_token"\
        .format(client_id=client_id,
                redirect_uri='http://localhost:8080',
                client_secret=client_secret,
                refresh_token=refresh_token)
    r = requests.post('https://login.live.com/oauth20_token.srf',
                      headers={'Content-type': 'application/x-www-form-urlencoded'},
                      data=body)
    j = json.loads(r.text)
    # print(json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')))
    # {
    #     "access_token": "EwA...Ag==",
    #     "expires_in": 3600,
    #     "refresh_token": "MCfJD..Cpyw$$",
    #     "scope": "wl.signin wl.offline_access onedrive.readwrite",
    #     "token_type": "bearer",
    #     "user_id": "AA...j30"
    # }
    return j


def login():
    """
    Try to login to OneDrive and acquire the required tokens.
    If a token file already exists, try to refresh the token.
    In the end: return the auth header which needs to be passed to the api calls
    :return: the auth header required in each oneDrive API call
    """

    keys = onedrive.json_io.load('onedrive_keys.json')
    client_id = keys.get('client_id')
    client_secret = keys.get('client_secret')

    token_file = 'tokens.json'
    if not os.path.isfile(token_file):
        auth_code = onedrive.auth.get_auth_code(client_id)
        tokens = onedrive.auth.get_tokens(auth_code, client_id, client_secret)
        onedrive.json_io.save(tokens, token_file)

    tokens = onedrive.json_io.load(token_file)
    new_tokens = onedrive.auth.refresh_tokens(tokens['refresh_token'], client_id, client_secret)
    onedrive.json_io.save(new_tokens, token_file)

    auth_header = {'Authorization': 'bearer ' + new_tokens['access_token']}
    return auth_header
