from envarify.types import SecretString


def test_secret_string():
    secret = SecretString("ABCD")

    assert str(secret) == "******"
    assert secret.reveal() == "ABCD"
    secret.erase()
    assert secret.reveal() == "\x00\x00\x00\x00"

    assert SecretString("XYZ") == SecretString("XYZ")
    assert SecretString("XYZ") != SecretString("XXX")
    assert SecretString("XYZ") in {SecretString("XYZ")}
