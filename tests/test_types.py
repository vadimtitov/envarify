import pytest

from envarify.types import AnyHttpUrl, HttpsUrl, HttpUrl, SecretString, Url


def test_secret_string():
    secret = SecretString("ABCD")

    assert str(secret) == "******"
    assert secret.reveal() == "ABCD"
    secret.erase()
    assert secret.reveal() == "\x00\x00\x00\x00"

    assert SecretString("XYZ") == SecretString("XYZ")
    assert SecretString("XYZ") != SecretString("XXX")
    assert SecretString("XYZ") in {SecretString("XYZ")}


@pytest.mark.parametrize(
    "url, url_type, valid",
    [
        ("lol://example.com", Url, True),
        ("http://192.168.1.1", Url, True),
        ("invalid-url", Url, False),
        ("http://example.com", HttpUrl, True),
        ("https://example.com", HttpUrl, False),
        ("http://example.com", HttpsUrl, False),
        ("https://example.com", HttpsUrl, True),
        ("http://example.com", AnyHttpUrl, True),
        ("https://example.com", AnyHttpUrl, True),
        ("ws://example.com", AnyHttpUrl, False),
        ("http://192.168.50.135:9696/", HttpUrl, True),
    ],
)
def test_url_is_valid(url, url_type, valid):
    if valid:
        assert url_type(url) == url
    else:
        with pytest.raises(ValueError):
            url_type(url)
