from onedrive import auth
from onedrive import hash_file
from onedrive import my_onedrive as drv


def main():
    path_local = 'C:/Users/info/Downloads/2006.09.10 Himmel Nürnberg.7z'
    path_remote_src = "/Backup/last/DigiCam/2006.09.10 Himmel Nürnberg.7z"
    path_remote_dst = "/Backup/new/DigiCam/2006.09.10 Himmel Nürnberg.7z"

    auth_header = auth.login()
    sha1_local = hash_file.sha1_file(path_local)
    sha1_remote_src = drv.get_sha1(file=path_remote_src, auth=auth_header)

    if sha1_local == sha1_remote_src:  # remote src is up to date
        drv.copy(src=path_remote_src, dst=path_remote_dst, auth=auth_header)  # overwrite target, create parent directories
        # do not upload
    else:
        # upload
        pass


if __name__ == "__main__":
    main()
