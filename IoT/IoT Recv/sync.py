from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.gmsservice import GMS
from Crypto.PublicKey import ECC
from Crypto.Signature import eddsa
import os
import logging
import datetime
import pysftp
import config

#TODO: Implement sending to IoT Server via sftp

SIG_BYTES = 64

cwd = os.path.dirname(os.path.realpath(__file__))

# Replace with address of NUS net/local IoT Server VM.
sftpServer = '192.168.232.143'

dongleDirectory = f"{cwd}/DongleKeys/"
serverDirectory = f"{cwd}/ServerGenKeys/"

ble = BLERadio()

GMS_connection = None

# Hardcoded mac address
found = {'MAC1': False, 'MAC2': False}

'''
Generates the directories for storing the public-private key pair.
'''
def generateDirectories():
    print("Generating Directories...")
    for dir in [dongleDirectory, serverDirectory, testServerDirectory]:
        if not os.path.exists(f"{dir}"):
            os.makedirs(dir)
            print(f"{dir} has been created.")
        else:
            print(f"{dir} already exists.")


"""
Instantiate the bootstrapped public key in IoT Dongle
"""
def setup():
    pub_pem = b''
    with open(serverDirectory+"defaultPublicKey.pem", "r") as f:
        pub_pem = f.read()
    pubSignKey = ECC.import_key(pub_pem)

    verifier = eddsa.new(pubSignKey, mode='rfc8032')
    return verifier

"""
Use the bootstrapped public key to verify the signature
Retrieve the generated public key of the IoT Dongle in clear
"""
def receiveAndVerifyPublicKey(GMS_connection, verifier):
    GMS_service = GMS_connection[GMS]
    GMS_service.write(b"sync")
    msg = GMS_service.read(256).rstrip(b'\x00')
    signature = msg[:SIG_BYTES]
    publicKey = msg[SIG_BYTES:]
    verifier.verify(publicKey, signature)
    return publicKey

"""
Save the generated public key of the IoT Dongle in PEM format and upload the pem file to the server
"""
def writeToPEM(publicKey, mac):
    donglePublicKey = eddsa.import_public_key(publicKey)
    pubKeyPem = donglePublicKey.export_key(format='PEM')
    filename = mac.replace(":", "") + ".pem"
    with open(dongleDirectory + filename, 'w') as f:
        f.write(pubKeyPem)
    print(f"Saved as PEM file in {dongleDirectory}")

    with pysftp.Connection(sftpServer, username=config.sftp_user, password=config.sftp_password) as sftp:
        # To store/upload files to server.
        with sftp.cd('/Receiver'):
            sftp.put(dongleDirectory + filename)

def connectToDongle(GMS_connection, mac, verifier):
    if GMS_connection and GMS_connection.connected:
        publicKey = receiveAndVerifyPublicKey(GMS_connection, verifier)
        writeToPEM(publicKey, mac)
    GMS_connection.disconnect()

def startScan(verifier):
    print("Scanning...")
    for adv in ble.start_scan(ProvideServicesAdvertisement, minimum_rssi=-95):
        if GMS in adv.services:
            mac = adv.address.string
            try:
                if found[mac] == False:
                    print(mac)
                    found[mac] = True
                    try:
                        GMS_connection = ble.connect(adv)
                        connectToDongle(GMS_connection, mac, verifier)
                    except:
                        logging.exception(datetime.datetime.now().time())
                        found[mac] = False
            except:
                pass
        if all(value == True for value in found.values()):
            break
    ble.stop_scan()

def exitScan():
    print("Finished retrieving IoT Dongle's public key.")
    print("...................................................................")

def main():
    generateDirectories()
    verifier = setup()
    startScan(verifier)
    exitScan()

if __name__ == "__main__":
    main()


# IoT Dongle Workflow (For setting up)
# 0. Bootstrap dongle with default keypairs generated by the server
# 1. Generate keypair upon sending sketch to dongle
# 2. Sync/setup.py (from Recv side) to connect to the dongle and retrieve generated public key of the dongle. 
#    Based on the receiver's message and code, 
# 	either send encrypted rssi using generated keypair ()
# 	or public key + signature using bootstrap key pair
# 3. If receiver requests for rssi before syncing, raise error to sync first.
# 4. IoT Dongle is now ready to send rssi to receiver

# IoT Recv Workflow (For setting up)
# 0. Pull bootstrap public key for dongle and keypair for receivers, server public key from IoT server
# 1. Run sync/setup.py 
# 2. Send Dongle PEM to IoT server (Not implemented yet)
# 3. Run IoTRecv.py (loop to connect and send to Dongle ephemeral public key and signature, then modify payload from Dongle to send to server)





        