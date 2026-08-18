import pytest

from src.scraper import _assert_public_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://192.168.1.5/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://localhost/",
    ],
)
def test_private_network_urls_are_rejected(url):
    with pytest.raises(ValueError):
        _assert_public_url(url)
