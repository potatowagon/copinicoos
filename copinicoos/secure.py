import base64
import os 
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def g_k(u):
    s = b'\xc5\xc2J]\xfd\xa5\xcc\x13\xc8VF\x17RxTm'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=s,
        iterations=1000,
        backend=default_backend()
    )

    k = []
    for i in range(len(u)):
        if i % 2:
            k.append(u[-i])
        else:
            k.append(u[i])
    ek = ''.join(k).encode()
    return base64.urlsafe_b64encode(kdf.derive(ek))

def encrypt(u, p):
    return Fernet(g_k(u)).encrypt(p.encode()).decode()

def decrypt(u, ep):
    return Fernet(g_k(u)).decrypt(ep.encode()).decode()