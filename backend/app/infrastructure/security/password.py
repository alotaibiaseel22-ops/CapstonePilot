import bcrypt

# Calls bcrypt directly rather than via passlib: passlib 1.7.4 (unmaintained since
# 2020) runs an internal self-test that crashes against bcrypt>=4.1's changed API
# ("password cannot be longer than 72 bytes" on passlib's own probe string, before
# ever hashing the real password) - a known, unresolved upstream incompatibility.

MAX_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")[:MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
