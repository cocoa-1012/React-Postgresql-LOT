# Connect to a GMS echo service

from http import server
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.gmsservice import GMS
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import ECC, RSA
from Crypto.Signature import eddsa
import hashlib, binascii
from ecdsa import curves, ECDH
from ecdsa.keys import SigningKey, VerifyingKey
import time
import logging
import datetime
import socket, os

LPORT = 1337
LHOST = "0.0.0.0"

LOCATION = b"LOCATION"
TOKEN = b"<TRACK2GATHER>"

KEY_BYTES = 16
EPHEMERAL_KEY_BYTES = 40
SIG_BYTES = 64

cwd = os.path.dirname(os.path.realpath(__file__))

dongleDirectory = f"{cwd}/DongleKeys/"
serverDirectory = f"{cwd}/ServerGenKeys/"

ble = BLERadio()

GMS_connection = None

serverPubPem = b''
with open(serverDirectory + 'serverPubKey.pem', 'r') as f:
    serverPubPem = f.read()
serverPubKey = RSA.import_key(serverPubPem)

recvPriPem = b''
with open(serverDirectory + 'recvPrivateKey.pem', 'r') as f:
    recvPriPem = f.read()
recvPriKey = ECC.import_key(recvPriPem)
signer = eddsa.new(recvPriKey, mode='rfc8032')

"""
Generate Ephemeral Keys on the IoT Recv to perform key exchange
"""
def generateEphemeralKeys():
    privKey = SigningKey.generate(curves.SECP160r1)
    pubKey = privKey.verifying_key
    return (privKey, pubKey)

"""
Send to Dongle the Ephemeral public key along with the signature
Receive the encrypted payload from the Dongle (This payload could have some errors as it is sent in packets but occassional loss should be acceptable)
"""
def writeReadToDongle(GMS_connection, pubKey):
    GMS_service = GMS_connection[GMS]
    pubKeyBytes = pubKey.to_string()
    sig = signer.sign(pubKeyBytes)
    GMS_service.write(pubKeyBytes + sig)
    time.sleep(5)
    msg = GMS_service.read(256).rstrip(b'\x00')
    return msg

"""
Split the message to the iv, tag, dongle's ephemeral public key and ciphertext
"""
def splitMsg(msg):
    iv = msg[:KEY_BYTES]
    tag = msg[KEY_BYTES: 2 * KEY_BYTES]
    ctPublicKey = VerifyingKey.from_string(msg[2 * KEY_BYTES:2 * KEY_BYTES + EPHEMERAL_KEY_BYTES], curves.SECP160r1)
    ct = msg[2 * KEY_BYTES + EPHEMERAL_KEY_BYTES:]
    return (iv, tag, ctPublicKey, ct)

"""
Generate the symmetric key from ECDH key exchange
"""
def generateSymKey(ctPublicKey, privKey):
    ecdh = ECDH(curves.SECP160r1, privKey, ctPublicKey)
    sharedSecret = ecdh.generate_sharedsecret_bytes()
    h = hashlib.sha256(sharedSecret)
    symKey = h.digest()[:KEY_BYTES]
    return symKey

"""
Create the new payload by adding tokens for splitting and adding the MAC and location to the dongle's payload, before encrypting with the server's public key
"""
def constructPayload(ct, symKey, iv, tag, mac):
    gcm = AES.new(symKey, AES.MODE_GCM, nonce=iv)
    gcm.decrypt_and_verify(ct, tag)
    message = ct + TOKEN + symKey + TOKEN + iv + TOKEN + tag + TOKEN + mac.encode() + TOKEN + LOCATION
    cipher = PKCS1_OAEP.new(serverPubKey)
    payload = cipher.encrypt(message)
    return payload

"""
Retrieve the dongle's public key to verify signature based on the dongle's MAC address
"""
def getDongleSignKey(mac):
    pub_pem = b''
    with open(dongleDirectory + mac.replace(":", "") + ".pem", "r") as f:
        pub_pem = f.read()
    pubSignKey = ECC.import_key(pub_pem)
    verifier = eddsa.new(pubSignKey, mode='rfc8032')
    return verifier

"""
For testing purposes, decrypt and verify plaintext from dongle
"""
def decryptAndVerification(symKey, iv, tag, ct, mac):
    gcm = AES.new(symKey, AES.MODE_GCM, nonce=iv)
    pt = gcm.decrypt_and_verify(ct, tag)
    signature = pt[:SIG_BYTES]
    plaintext = pt[SIG_BYTES:]
    verifier = getDongleSignKey(mac)
    verifier.verify(plaintext, signature)
    return plaintext

"""
Send the encrypted payload to the server
"""
def sendPayload(payload):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((LHOST, LPORT))
        s.sendall(payload)

def connectToDongle(GMS_connection, mac):
    if GMS_connection and GMS_connection.connected:
        print(mac)
        privKey, pubKey = generateEphemeralKeys()
        msg = writeReadToDongle(GMS_connection, pubKey)
        iv, tag, ctPublicKey, ct = splitMsg(msg)
        symKey = generateSymKey(ctPublicKey, privKey)
        payload = constructPayload(ct, symKey, iv, tag, mac)
        sendPayload(payload)

        # To verify on the receiver side
        plaintext = decryptAndVerification(symKey, iv, tag, ct, mac)
        print(plaintext)
    GMS_connection.disconnect()
    

# Structure: 16 (iv), 16 (tag), 40(public key), rest(ct): 64(signature), rest(pt)

def main(GMS_connection):
    while True:
        if not GMS_connection:
            print("Trying to connect...")
            try:
                for adv in ble.start_scan(ProvideServicesAdvertisement, minimum_rssi=-95):
                    if GMS in adv.services:
                        GMS_connection = ble.connect(adv)
                        connectToDongle(GMS_connection, adv.address.string)
                ble.stop_scan()
            except ValueError:
                print("Invalid Signature")
                GMS_connection.disconnect()
            except KeyboardInterrupt:
                exit()
            except:
                logging.exception(datetime.datetime.now().time())
                if GMS_connection and GMS_connection.connected:
                    GMS_connection.disconnect()
            finally:
                GMS_connection = None
                ble.stop_scan()

if __name__ == "__main__":
    main(GMS_connection)






