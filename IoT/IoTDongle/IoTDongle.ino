
#include <AES.h>
#include <AuthenticatedCipher.h>
#include <BigNumberUtil.h>
#include <BLAKE2b.h>
#include <BLAKE2s.h>
#include <BlockCipher.h>
#include <ChaCha.h>
#include <ChaChaPoly.h>
#include <Cipher.h>
#include <Crypto.h>
#include <CTR.h>
#include <Curve25519.h>
#include <EAX.h>
#include <Ed25519.h>
#include <GCM.h>
#include <GF128.h>
#include <GHASH.h>
#include <Hash.h>
#include <HKDF.h>
#include <KeccakCore.h>
#include <NoiseSource.h>
#include <OMAC.h>
#include <P521.h>
#include <Poly1305.h>
#include <RNG.h>
#include <SHA224.h>
#include <SHA256.h>
#include <SHA3.h>
#include <SHA384.h>
#include <SHA512.h>
#include <SHAKE.h>
#include <XOF.h>
#include <XTS.h>

#include <types.h>
#include <uECC.h>
#include <uECC_vli.h>

#include <RFduinoBLE.h>

bool rssidisplay;

const struct uECC_Curve_t * curve = uECC_secp160r1();

const char *id = "GENERIC_ID";

int curr_rssi = -100;
const int KEY_BYTES = 16;
const int MSG_BYTES = 4;
const int PUB_KEY_BYTES = 40;
const int PRI_KEY_BYTES = 21;
const int SEC_KEY_BYTES = 20;
const int SIG_BYTES = 64;
const int HASH_BYTES = 32;
const int SIGN_KEY_BYTES = 32;

uint8_t pri_sign_key[SIGN_KEY_BYTES];
uint8_t pub_sign_key[SIGN_KEY_BYTES];

uint8_t def_pri_key[SIGN_KEY_BYTES] = "REDACTED";
uint8_t def_pub_key[SIGN_KEY_BYTES] = "REDACTED";
uint8_t verify_recv_key[SIGN_KEY_BYTES] = "REDACTED";

char recv_msg[PUB_KEY_BYTES + SIG_BYTES + 1];
uint8_t pub_recv[PUB_KEY_BYTES];
int public_count = 0;
int count = 1;

static int getRNG(uint8_t *dest, unsigned size) {
  // Use the least-significant bits from the ADC for an unconnected pin (or connected to a source of
  // random noise). This can take a long time to generate random data if the result of analogRead(0)
  // doesn't change very frequently.
  while (size) {
    //uint8_t val = spritz_random8(&rng_ctx);
    uint8_t val;
    RNG.rand(&val, 1);
    *dest = val;
    ++dest;
    --size;
  }
  return 1;
}

void setup() {
  RFduinoBLE.advertisementData = "echo";
  RFduinoBLE.deviceName = id;           // Specify BLE device name
  RFduinoBLE.advertisementInterval = 50;
  RFduinoBLE.txPowerLevel = +4;
  RFduinoBLE.begin();                            // Start the BLE stack
  Serial.begin(9600);                            // Debugging to the serial port
  Serial.print(id);
  Serial.println(" device restarting...");

  RNG.begin(id);
  uECC_set_rng(&getRNG);

  Ed25519::generatePrivateKey(pri_sign_key);
  Ed25519::derivePublicKey(pub_sign_key, pri_sign_key);
}

void RFduinoBLE_onConnect() {
  Serial.println("Start connection...");
  rssidisplay = true;
}

void RFduinoBLE_onDisconnect() {
  Serial.println("Disconnection...");
}

void convertToHexString(uint8_t *int_arr, char *str_arr, int key_length) {
  int k = 0;
  for (uint8_t i = 0; i < (uint8_t)(key_length); i++) {
    char buf[3];
    sprintf(buf, "%02X", int_arr[i]);
    str_arr[k] = buf[0];
    str_arr[k + 1] = buf[1];
    k += 2;
  }
  str_arr[k] = '\0';
}

int generateKeys(uint8_t *pub_key, uint8_t *pub_recv, uint8_t *key, uint8_t *iv) {
  uint8_t priv_key[PRI_KEY_BYTES];
  uint8_t secret[SEC_KEY_BYTES];
  int error = uECC_make_key(pub_key, priv_key, curve);
  if (!error) {
    Serial.print("make key() failed (1)\n");
    return 0;
  }

  int r = uECC_shared_secret(pub_recv, priv_key, secret, curve);
  if (!r) {
    Serial.print("shared_secret() failed (1)\n");
    return 0;
  }

  SHA256 hash = SHA256();
  hash.update(secret, SEC_KEY_BYTES);
  hash.finalize(key, KEY_BYTES);

  for (int i = 0; i < KEY_BYTES; i++) {
    uint8_t val;
    RNG.rand(&val, 1);
    iv[i] = val;
  }

  return 1;
}

int convertToString(char *char_arr, uint8_t *int_arr) {
  String str_rssi = String(curr_rssi);
  str_rssi.toCharArray(char_arr, MSG_BYTES);

  int actual_msg_bytes = strlen(char_arr);
  for (uint8_t i = 0; i < actual_msg_bytes; i++) {
    int_arr[i] = (uint8_t) char_arr[i];
  }
  return actual_msg_bytes;
}

void encryptAndTag(uint8_t *key, uint8_t *iv, uint8_t *ct, uint8_t *pt, uint8_t *tag, int pt_bytes) {
  GCM<AES128> gcm;
  gcm.setKey(key, KEY_BYTES);
  gcm.setIV(iv, KEY_BYTES);
  gcm.encrypt(ct, pt, pt_bytes);
  gcm.computeTag(tag, KEY_BYTES);
}

void constructMsg(uint8_t *iv, uint8_t *ct, uint8_t *tag, uint8_t *pub_key, char *msg, int msg_length, int pt_bytes) {
  memcpy(msg, (char *)iv, KEY_BYTES);
  memcpy(msg + KEY_BYTES, (char *)tag, KEY_BYTES);
  memcpy(msg + 2 * KEY_BYTES, (char *)pub_key, PUB_KEY_BYTES);
  memcpy(msg + 2 * KEY_BYTES + PUB_KEY_BYTES, (char *)ct, pt_bytes);
  msg[msg_length - 1] = '\0';
}

void sendMsg(char *msg, int msg_length) {
  int curr = 0;
  int bytes = 20;
  while (RFduinoBLE.send(msg + curr, bytes)) {
    curr += bytes;
    if (msg_length - curr < 20) {
      bytes = msg_length - curr;
    }
  }
}

void RFduinoBLE_onReceive(char *data, int len) {
  data[len] = 0;

  if (!strcmp(data, "sync")) {
    Serial.println("syncing");
    uint8_t sig[SIG_BYTES];
    Ed25519::sign(sig, def_pri_key, def_pub_key, (char *) pub_sign_key, SIGN_KEY_BYTES);
    int msg_length = SIG_BYTES + SIGN_KEY_BYTES + 1;
    char msg[msg_length];
    memcpy(msg, (char *)sig, SIG_BYTES);
    memcpy(msg + SIG_BYTES, (char *)pub_sign_key, SIGN_KEY_BYTES);
    msg[msg_length - 1] = '\0';
    sendMsg(msg, msg_length);
    return;
  }

  memcpy(recv_msg + public_count, data, len);
  public_count += len;
  if (public_count < PUB_KEY_BYTES + SIG_BYTES) {
    return;
  } else {
    public_count = 0;
  }
  recv_msg[PUB_KEY_BYTES + SIG_BYTES] = '\0';
  uint8_t recv_sig[SIG_BYTES];
  memcpy(pub_recv, (uint8_t *)recv_msg, PUB_KEY_BYTES);
  memcpy(recv_sig, (uint8_t *)(recv_msg + PUB_KEY_BYTES), SIG_BYTES);
  if (!Ed25519::verify(recv_sig, verify_recv_key, pub_recv, PUB_KEY_BYTES)) {
    Serial.println("Invalid Signature");
    return;
  }

  uint8_t pub_key[PUB_KEY_BYTES];
  uint8_t key[KEY_BYTES];
  uint8_t iv[KEY_BYTES];

  if (!generateKeys(pub_key, pub_recv, key, iv)) {
    Serial.println("Generate Keys Failed");
    return;
  }

  char char_arr_rssi[MSG_BYTES];
  uint8_t int_arr_rssi[MSG_BYTES];
  int actual_msg_bytes = convertToString(char_arr_rssi, int_arr_rssi);

  uint8_t sig[SIG_BYTES];
  Ed25519::sign(sig, pri_sign_key, pub_sign_key, char_arr_rssi, actual_msg_bytes);

  int pt_bytes = SIG_BYTES + actual_msg_bytes;
  uint8_t combined_pt[pt_bytes];
  uint8_t ct[pt_bytes];
  uint8_t tag[KEY_BYTES];

  memcpy(combined_pt, sig, SIG_BYTES);
  memcpy(combined_pt + SIG_BYTES, int_arr_rssi, actual_msg_bytes);

  encryptAndTag(key, iv, ct, combined_pt, tag, pt_bytes);

  int msg_length = PUB_KEY_BYTES + 2 * KEY_BYTES + pt_bytes + 1;
  char b_msg[msg_length];

  constructMsg(iv, ct, tag, pub_key, b_msg, msg_length, pt_bytes);
  sendMsg(b_msg, msg_length);
}

void RFduinoBLE_onRSSI(int rssi) {
  if (rssidisplay) {
    Serial.print("RSSI is ");
    Serial.println(rssi);                        // print rssi value
    curr_rssi = rssi;
    rssidisplay = false;
  }
}

void loop() {
  RFduino_ULPDelay( SECONDS(0.5) );                // Ultra Low Power delay for 0.5 second
  RNG.loop();
}
