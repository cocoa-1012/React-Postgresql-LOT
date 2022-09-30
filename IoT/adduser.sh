#!/bin/bash

# Replace with actual password.
sftp_password="REDACTED"
sftp_user=$1

useradd -m -s /bin/bash "$sftp_user"
echo "$sftp_user:$sftp_password" | sudo chpasswd
