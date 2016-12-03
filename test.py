from my_onedrive import auth
from my_onedrive import hash_file
from my_onedrive import my_onedrive as drv


def main():
    auth_header = auth.login()

    sha1_local = hash_file.sha1_file('C:/Users/info/Downloads/2006.09.10 Himmel Nürnberg.7z')
    remote_path = "/DigiCam/2006.09.10 Himmel Nürnberg.7z"
    drv.copy_if_same_hash(
        src="/Backup/last" + remote_path,
        dst="/Backup/new" + remote_path,
        sha1_local=sha1_local,
        auth_header=auth_header )

if __name__ == "__main__":
    main()
