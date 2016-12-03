from my_onedrive import auth
from my_onedrive import hash_file
from my_onedrive import my_onedrive


def main():
    auth_header = auth.login()

    sha1_local = hash_file.sha1_file('C:/Users/info/Downloads/2006.09.10 Himmel Nürnberg.7z')
    file_path = "/DigiCam/2006.09.10 Himmel Nürnberg.7z"
    my_onedrive.onedrive_copy_if_same_hash(
        src="/Backup/last" + file_path,
        dst="/Backup/new" + file_path,
        sha1_local=sha1_local,
        auth_header=auth_header )

if __name__ == "__main__":
    main()
