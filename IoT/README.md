# IoT Component Documentation

## Manual Prerequisites

The only manual setup required would be the changes to the credentials.

### SFTP User Credentials

In the `add_user.sh` file, modify line 3 and replace `REDACTED` with the intended `sftp` user password.

```
Line 0: #!/bin/bash
Line 1:
Line 2: # Replace with actual password.
Line 3: sftp_password="REDACTED"
Line 4: sftp_user=$1
Line 5:
Line 6: useradd -m -s /bin/bash "$sftp_user"
Line 7: echo "$sftp_user:$sftp_password" | sudo chpasswd
```

Next, configure the `config.py` and modify line 5, replacing the `REDACTED` with the intended `sftp` user password mentioned above.

```
Line 0: # Logtail
Line 1: source_token="REDACTED"
Line 2:
Line 3: # SFTP
Line 4: sftp_user="sftp"
Line 5: sftp_password="REDACTED"
```

### Logtail Source Token

For the logtail token, you will need to obtain from the Logtail's dashboard. Then paste it into line 1 to replace the `REDACTED`.

```
Line 0: # Logtail
Line 1: source_token="REDACTED"
Line 2:
Line 3: # SFTP
Line 4: sftp_user="sftp"
Line 5: sftp_password="REDACTED"
```

### iptables IP whitelist

To allow only the IoT receiver's IP to communicate with the IoT Server, we need to modify the `recvIP` value found in the `pre-setup.sh` to the IoT receiver's IP address.
```
sudo cp SFTP/sshd_config /etc/ssh/sshd_config
sudo systemctl restart sshd

# Replace with receiver's IP, i.e. the PC's IP.
recvIP="192.168.232.1"
```

## Setting up

> IMPORTANT :warning: - If you intend to run this script on the NUS server, please make sure you keep two terminals open. So that the iptables configuration will not lock you out. The iptables has only been tested on non-NUS domain set up and yet to be tested on NUS domain. So, omit the iptables if needed.

> Assuming you have done `git clone` or copied the repository to `~/` where `~` refers to your home directory.

Once the manual [Pre-requisites](#manual-prerequisites) are done.
We can start setting up from the home directory (`~/`)
```
cd IFS4205-AY2223-S1-Team02-Track2Gather/src/Track2Gather-WebApp/IoT/
```

Then run the following in the terminal. This will help to run the setup scripts and starting of the IoT Server socket. Do also note, you will be prompted with the user's password.
```
./pre-setup.sh
```

After running the script, the terminal should appear similar to output below and "hangs" there. This is normal as the IoT Server has started immediately after the set up is done.
```
...
Some very long outputs from installations
...
Generating Directories...
/home/<user>/IFS4205-AY2223-S1-Team02-Track2Gather/src/Track2Gather-WebApp/IoT/Share/ has been created.
/home/<user>/IFS4205-AY2223-S1-Team02-Track2Gather/src/Track2Gather-WebApp/IoT/Secret/ has been created.
/home/<user>/IFS4205-AY2223-S1-Team02-Track2Gather/src/Track2Gather-WebApp/IoT/ServerGenKeys/ has been created.
Finished the required directories.
Finished setting up IoT Server's RSA key pair and ED25519 key pairs.
Goodbye.
...................................................................
```

## IPtables configuration

> Note that the `pre-setup.sh` runs the a copy of the contents in `iptables-rules.txt`. The `iptables-rules.txt` are just for nice formatting and rules collation.

The configuration for the iptables are included in the `iptables-rules.txt` as a sample and shown below. This iptables configuration is also included in the `pre-setup.sh` script to set up iptable rules.

```
# Drop everything in-bound by default.
sudo iptables -P INPUT DROP

# Track state of connection and allow those.
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow ICMP.
sudo iptables -A INPUT -p icmp -j ACCEPT

# Enabling DNS Resolutions. (For logtail and perhaps nus domain)
sudo iptables -A INPUT -p udp --sport 53 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 53 -j ACCEPT

# Allow Receivers to SFTP and connect to IoT Server.
sudo iptables -A INPUT -p tcp -j ACCEPT -s 192.168.232.1 --dport 22
sudo iptables -A INPUT -p tcp -j ACCEPT -s 192.168.232.1 --dport 1337

```

## Sanity Check

To do a sanity check, you should be able to connect to the port and check the logs outputted on Logtail dashboard.

```
nc <IP> 1337

# After connecting (you will see no responses or anything), just type and send in anything e.g.
I am a test for sanity purposes.
```


## Setting up Dongles and Receivers

After setting up the server, you can begin to configure the Dongles and Receivers.

Before that, all Receivers (simulated by laptops) should have a config.py (in the directory which contains all IoT Receiver files cloned from the repository) with a registered sftp user and password as shown:
```
sftp_user="REDACTED"
sftp_password="REDACTED"
```

There should be a designated Receiver which is able to upload sketches onto the Dongle. For this Receiver, you can run `python bootstrap.py --all` and get the following output:
```
Retrieving Keys from Server...
Retrieved serverPubKey.pem
Retrieved recvPrivateKey.pem
Retrieved recvPublicKey.pem
Retrieved defaultPrivateKey.pem
Retrieved defaultPublicKey.pem
...................................................................
Please copy this private key into the Arduino code, variable REDACTED:
{REDACTED}
...................................................................
Please copy this public key into the Arduino code, variable REDACTED:
{REDACTED}
...................................................................
```
Copying the keys into the Arduino code and uploading the sketch to the Dongles will complete the setup process for the Dongles.

For all other Receivers, you can simply run `python bootstrap.py` to retrieve the files.

The designated Receiver should run `python sync.py` to sync the key files with the Dongles and the Server and complete the setup process.

## Unit Testing

In the `test` directory, run the following command
```
python -m unittest discover -s . -p "IoT*Tests.py"
```

This will run the `IoTServerTests.py` file that performs unit testing for the `IoTServer.py`.

## TODO

1. Integrate with DB end to pass data received on IoTServer into the DB.
2. Continue with Unit Testing of cases.
3. Write Github Actions workflow for automating testing of unit tests found in `test/` directory.
