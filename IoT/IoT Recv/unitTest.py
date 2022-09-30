import unittest
import IoTRecv
from ecdsa import curves, ECDH
from ecdsa.keys import SigningKey, VerifyingKey
import pickle
import sync

correct_payload_dict = pickle.load(open("test_payload1.pickle", "rb" ))
wrong_payload_dict = pickle.load(open("test_payload2.pickle", "rb" ))

"""
dictionary_structure: {
    'payload': b'Dongle's Encrypted message', 
    'ct': b'Split Ciphertext', 
    'iv': b'IV used for the encryption', 
    'tag': b'Tag generated using AES GCM', 
    'donglePublicKey': b'The ephemeral public key from dongle used to generate symmetric key', 
    'recvPublicKey': b'The ephemeral public key from recv used to generate symmetric key', 
    'recvPrivateKey': b'The ephemeral private key from recv used to generate symmetric key', 
    'secretKey': b'Symmetric Key generated from the ephemeral keypairs', 
    'pt': b'data + signature', 
    'signature': b'signature of the dongle from the data', 
    'data': b'data sent (RSSI)',
    'mac' : b'mac address of dongle', 
    'location': b'location of recv',
    'encryptedPayload': b'Recv's Encrypted payload to server'}
"""


class TestRecv(unittest.TestCase):
    def test_symkey_success(self):
        donglePublicKey = correct_payload_dict['donglePublicKey']
        recvPrivateKey = correct_payload_dict['recvPrivateKey']
        privKey = SigningKey.from_string(recvPrivateKey, curves.SECP160r1)
        pubKey = VerifyingKey.from_string(donglePublicKey, curves.SECP160r1)
        secretKey = IoTRecv.generateSymKey(pubKey, privKey)
        self.assertEqual(correct_payload_dict['secretKey'], secretKey)
    def test_symkey_failure(self):
        donglePublicKey = wrong_payload_dict['donglePublicKey']
        recvPrivateKey = wrong_payload_dict['recvPrivateKey']
        privKey = SigningKey.from_string(recvPrivateKey, curves.SECP160r1)
        pubKey = VerifyingKey.from_string(donglePublicKey, curves.SECP160r1)
        secretKey = IoTRecv.generateSymKey(pubKey, privKey)
        self.assertNotEqual(correct_payload_dict['secretKey'], secretKey)
    def test_split_msg_success(self):
        test_iv, test_tag, test_donglePubKey, test_ct = IoTRecv.splitMsg(correct_payload_dict['payload'])
        self.assertEqual(test_iv, correct_payload_dict['iv'])
        self.assertEqual(test_tag, correct_payload_dict['tag'])
        self.assertEqual(test_donglePubKey.to_string(), correct_payload_dict['donglePublicKey'])
        self.assertEqual(test_ct, correct_payload_dict['ct'])
    def test_split_msg_failure(self):
        test_iv, test_tag, test_donglePubKey, test_ct = IoTRecv.splitMsg(wrong_payload_dict['payload'])
        self.assertNotEqual(test_iv, correct_payload_dict['iv'])
        self.assertNotEqual(test_tag, correct_payload_dict['tag'])
        self.assertNotEqual(test_donglePubKey.to_string(), correct_payload_dict['donglePublicKey'])
        self.assertNotEqual(test_ct, correct_payload_dict['ct'])


