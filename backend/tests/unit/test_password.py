from app.infrastructure.security.password import hash_password, verify_password


def test_hash_and_verify_roundtrip():
    password_hash = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", password_hash)


def test_wrong_password_does_not_verify():
    password_hash = hash_password("correct-horse-battery-staple")
    assert not verify_password("wrong-password", password_hash)


def test_hash_is_not_the_plaintext():
    password_hash = hash_password("correct-horse-battery-staple")
    assert password_hash != "correct-horse-battery-staple"
