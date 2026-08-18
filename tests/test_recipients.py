from src.main import normalize_recipients


def test_normalize_recipients_from_list():
    delivery = {
        "recipients": [
            "reader.one@example.com",
            " reader.two@example.com ",
            "reader.one@example.com",
        ]
    }
    assert normalize_recipients(delivery) == [
        "reader.one@example.com",
        "reader.two@example.com",
    ]


def test_normalize_recipients_from_string():
    delivery = {
        "recipients": "reader.one@example.com, reader.two@example.com\nreader.three@example.com"
    }
    assert normalize_recipients(delivery) == [
        "reader.one@example.com",
        "reader.two@example.com",
        "reader.three@example.com",
    ]


def test_legacy_single_recipient_still_works():
    assert normalize_recipients({"recipient": "reader@example.com"}) == [
        "reader@example.com"
    ]
