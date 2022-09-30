#!/bin/bash
# Before running: chmod +x pre-setup.sh
# Syntax: ./pre-setup-IoTServer.sh

# Install necessary system packages.
sudo apt install git -y
sudo apt install python3-pip -y
sudo apt install ssh -y

cd ~
# Manually copy the project directory to home directory (~/)
# Temporary solution, since repo is private.
# git clone https://github.com/Kair0s3/TestingDevSecOps.git
cd IFS4205-AY2223-S1-Team02-Track2Gather/src/Track2Gather-WebApp/IoT

# Set up SFTP Server https://www.digitalocean.com/community/tutorials/how-to-enable-sftp-without-shell-access-on-ubuntu-20-04
# Using another bash script to create user, password for sftp.
sudo ./adduser.sh sftp
sudo mkdir -p /home/sftp/Dongles/
sudo mkdir -p /home/sftp/Server/
sudo chown root:root /home/sftp
sudo chmod 755 /home/sftp
sudo chown sftp:sftp /home/sftp/Dongles
sudo chown sftp:sftp /home/sftp/Server
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bk
sudo cp SFTP/sshd_config /etc/ssh/sshd_config
sudo systemctl restart sshd

# Replace with receiver's IP, i.e. the PC's IP.
recvIP="192.168.232.1"

# iptables rules
#######################################################################
# Drop everything in-bound by default.
sudo iptables -P INPUT DROP

# Track state of connection and allow those.
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow ICMP.
sudo iptables -A INPUT -p icmp -j ACCEPT

# Enabling DNS Resolutions. (For logtail and perhaps nus domain)
sudo iptables -A INPUT -p udp --sport 53 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 53 -j ACCEPT

# Allow Receivers to SFTP and connect to IoT Server. i.e. 192.168.232.1
sudo iptables -A INPUT -p tcp -j ACCEPT -s $recvIP --dport 22
sudo iptables -A INPUT -p tcp -j ACCEPT -s $recvIP --dport 1337
#######################################################################

# Install python packages.
pip3 install -r requirements.txt

# Generate RSA Key pairs.
python3 generateRSAKeypair.py

# Copy the keypairs to the SFTP public directories.
sudo cp Share/serverPubKey.pem /home/sftp/Server/
sudo chown sftp:sftp /home/sftp/Server/serverPubKey.pem

# Finally, start the IoT Server.
python3 IoTServer.py
