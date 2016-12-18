from onedrive import auth
from onedrive import api as drv


def main():
    auth_header = auth.login()

    # local = hash_file.crc32_file("F:/OneDrive/Backup/current/DigiCam Raw/2015.10.12 Eng Panoramaweg.7z")
    remote = drv.get_sha1("/Backup/last/DigiCam Raw/2015.10.12 Eng Panoramaweg.7z", auth_header)
    print(remote)

    # path_local = 'C:/Users/info/Downloads/2006.09.10 Himmel Nürnberg.7z'
    # path_remote_src = "/Backup/last/DigiCam/2006.09.10 Himmel Nürnberg.7z"
    # path_remote_dst = "/Backup/new/DigiCam/2006.09.10 Himmel Nürnberg.7z"
    #
    # sha1_local = hash_file.sha1_file(path_local)
    # sha1_remote_src = drv.get_sha1(file=path_remote_src, auth=auth_header)
    #
    # if sha1_local == sha1_remote_src:  # remote src is up to date
    #     drv.copy(src=path_remote_src, dst=path_remote_dst, auth=auth_header)  # overwrite target, create parent directories
    #     # do not upload
    # else:
    #     # upload
    #     pass


if __name__ == "__main__":
    main()
