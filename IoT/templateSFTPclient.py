import pysftp, os
import config

# Before running, make sure to SSH once, to make sure the host key is stored on your registry.

cwd = os.path.dirname(os.path.realpath(__file__))

# Replace with address of NUS net/local IoT Server VM.
sftpServer = '192.168.232.143'

with pysftp.Connection(sftpServer, username=config.sftp_user, password=config.sftp_password) as sftp:
    # To get files from server.
    with sftp.cd('/Server'):           # temporarily chdir to allcode
        sftp.get('serverPubKey.pem', f"{cwd}/serverPubKey.pem")         # get a remote file
    # To store/upload files to server.
    with sftp.cd('/Dongles'):
        sftp.put(f"{cwd}/serverPubKey.pem", "hellothere.pem")
