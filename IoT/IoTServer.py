from logtail import LogtailHandler
import config
import logging
import socket, os, sys
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA, ECC
from Crypto.Signature import DSS, eddsa
from Crypto.Hash import SHA256

handler = LogtailHandler(source_token=config.source_token)

logger = logging.getLogger(__name__)
logger.handlers = []
logger.setLevel(logging.INFO)
logger.addHandler(handler)

cwd = os.path.dirname(os.path.realpath(__file__))

# To be changed to file location containing the server's private key.
secretDirectory = f"{cwd}/Secret/"

# To be changed to SFTP directory for dongle's public key.
donglesDirectory = f"{cwd}/Receiver/"

LPORT = 1337
LHOST = "0.0.0.0"

SIG_BYTES = 64

'''
Returns the data portion of the unencrypted payload.
'''
def getData(payload):
    data = payload[64:]
    return data

'''
Verifies the signature of the data.
Returns whether the signature is valid. (Ensure no changes in data and verified signature)
'''
def verifySignature(payload, macAddress):
    filename = macAddress.decode().replace(":", "") + ".pem"
    f = open(f'{donglesDirectory}{filename}','rb')
    donglePublicKey = ECC.import_key(f.read())
    signature = payload[:SIG_BYTES]
    data = payload[SIG_BYTES:]
    verifier = eddsa.new(donglePublicKey, mode='rfc8032')
    try:
        verifier.verify(data, signature)
        return True
    except ValueError:
        return False
'''
Performs AES GCM decryption using the symmetric key.
Returns the decrypted payload containing unencrypted data and signature.
'''
def decrypt_AES_GCM(encryptedData, nonce, authTag, symmetricKey):
    aesCipher = AES.new(symmetricKey, AES.MODE_GCM, nonce)
    actualPayload = aesCipher.decrypt_and_verify(encryptedData, authTag)
    return actualPayload

'''
Decrypts the second layer of encryption
using the symmetric key obtained from first decryption.
Returns the mac address of the dongle and the decrypted payload (data + signature).
'''
def decryptWithSymmetricKey(layerTwoPayload):
    split = layerTwoPayload.split(b"<TRACK2GATHER>")
    encryptedData = split[0]
    symmetricKey = split[1]
    nonce = split[2]
    authTag = split[3]
    macAddress = split[4]
    location = split[5]
    return macAddress, decrypt_AES_GCM(encryptedData, nonce, authTag, symmetricKey), location

'''
Decrypts the first outer layer of encryption
using Server's private key.
Returns the second layer payload.
'''
def decryptWithServerPrivateKey(encryptedPayload):
    privKeyFile = "serverPrivKey.pem"
    f = open(f'{secretDirectory}{privKeyFile}','rb')
    key = RSA.import_key(f.read())
    cipher = PKCS1_OAEP.new(key)
    layerTwoPayload = cipher.decrypt(encryptedPayload)
    return layerTwoPayload

'''
Starts the IoT Server and listens for IoT Receiver
to connect and send the encrypted payload.
'''
def startIotServer():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((LHOST, LPORT))
    server.listen(5)
    logger.info('Started IoT Server Socket.')
    while 1:
        logger.info("IoT Server is waiting for a connection.")
        (conn, address) = server.accept()
        logger.info("Connection to IoT Server has been established.", extra={
            'Host': address[0]
        })
        while 1:
            forceReset = False
            try:
                data = conn.recv(1024)
            except ConnectionResetError:
                logger.error("A connection to IoT Server was forcibly closed by client.", extra={
                    'Host': address[0]
                })
                forceReset = True
                break
            if not data:
                break
            try:
                layerTwoPayload = decryptWithServerPrivateKey(data)
            except:
                logger.critical('Decryption of the first layer failed.', extra = {
                    'Host': address[0],
                    "Data" : data
                })
                break
            try:
                macAddress, payload, location = decryptWithSymmetricKey(layerTwoPayload)
            except:
                logger.critical('Decryption of the second layer failed.', extra = {
                    'Host': address[0],
                    "Data" : layerTwoPayload,
                    "MAC-Address" : macAddress,
                    "Location" : location
                })
                break
            if verifySignature(payload, macAddress):
                data = getData(payload)
                print(data)
            else:
                logger.critical('Invalid Signature', extra = {
                    'Host': address[0],
                    "Data" : payload,
                    "MAC-Address" : macAddress,
                    "Location" : location
                })
        conn.close()
        if not forceReset:
            logger.info("Connection to IoT Server has ended", extra={
                'Host': address[0]
            })

def main():
    try:
        startIotServer()
    except KeyboardInterrupt:
        logger.info("IoT Server has been stopped by keyboard interrupt.")

if __name__ == "__main__":
    main()
