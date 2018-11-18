"""
Support for assymetric password encryption and decryption. Use with::

    hash_value = core4.util.crypt.pwd_context.hash(clear_text)
    assert core4.util.crypt.pwd_context.verify(clear_text, hash_value))
"""
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "des_crypt"],
    deprecated="auto",
)
