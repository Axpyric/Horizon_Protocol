#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import os, json, base64
from getpass import getpass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def _derive_key(passphrase: str, salt: bytes, n: int, r: int, p: int):
    kdf = Scrypt(salt=salt, length=32, n=n, r=r, p=p)
    return kdf.derive(passphrase.encode('utf-8'))

def generate_key_file(out_path: str = "keys/private_ed25519.enc", passphrase: str = None, n: int = 32768, r: int = 8, p: int = 1):
    if passphrase is None:
        passphrase = getpass("Enter passphrase to encrypt new Ed25519 key: ")
        pass2 = getpass("Confirm: ")
        if passphrase != pass2:
            raise SystemExit("Passphrases do not match")
    sk = Ed25519PrivateKey.generate()
    raw = sk.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    pub = sk.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    salt = os.urandom(16)
    key = _derive_key(passphrase, salt, n, r, p)
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aes.encrypt(nonce, raw, None)
    envelope = {
        "version": "1",
        "kdf": "scrypt",
        "kdf_params": {"salt": base64.b64encode(salt).decode(), "n": n, "r": r, "p": p},
        "cipher": "AES-GCM",
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "public_key": base64.b64encode(pub).decode()
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    print("Wrote encrypted key to", out_path)
    return envelope

if __name__ == "__main__":
    generate_key_file()
