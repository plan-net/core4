from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "des_crypt"],
    deprecated="auto",
)
