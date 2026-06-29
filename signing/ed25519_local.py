#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import json, base64, hashlib
from getpass import getpass
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

class Ed25519LocalProvider:
    def __init__(self, path: str, passphrase: Optional[str] = None):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError("Key file not found at: " + str(self.path))
        self.passphrase = passphrase
        self._priv = None
        self._pub = None
        self._keyid = None

    def _load_envelope(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _derive_key(self, passphrase: str, salt: bytes, n: int, r: int, p: int):
        kdf = Scrypt(salt=salt, length=32, n=n, r=r, p=p)
        return kdf.derive(passphrase.encode("utf-8"))

    def unlock(self):
        env = self._load_envelope()
        salt = base64.b64decode(env["kdf_params"]["salt"])
        n = env["kdf_params"]["n"]; r = env["kdf_params"]["r"]; p = env["kdf_params"]["p"]
        nonce = base64.b64decode(env["nonce"])
        ciphertext = base64.b64decode(env["ciphertext"])
        if self.passphrase is None:
            self.passphrase = getpass("Enter passphrase to unlock signing key: ")
        key = self._derive_key(self.passphrase, salt, n, r, p)
        aes = AESGCM(key)
        try:
            raw = aes.decrypt(nonce, ciphertext, None)
        except Exception:
            raise ValueError("Decryption failed (bad passphrase or corrupted file)")
        self._priv = Ed25519PrivateKey.from_private_bytes(raw)
        self._pub = self._priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self._keyid = hashlib.sha256(self._pub).hexdigest()

    def sign(self, message: bytes) -> Dict[str, Any]:
        if not self._priv:
            self.unlock()
        sig = self._priv.sign(message)
        return {"method":"Ed25519","keyid":self._keyid,"value":base64.b64encode(sig).decode(),"created_at":__import__("datetime").datetime.utcnow().isoformat()+"Z"}

    def verify_with_pub(self, message: bytes, signature: Dict[str,str], pub_b64: str) -> bool:
        try:
            sig = base64.b64decode(signature["value"])
            pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64))
            pub.verify(sig, message)
            return True
        except Exception:
            return False
