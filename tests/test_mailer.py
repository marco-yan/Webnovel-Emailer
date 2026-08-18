from src.mailer import build_message


def test_build_message():
    msg = build_message(
        "sender@example.com",
        "reader@example.com",
        "Reading batch",
        "Chapter 1",
    )
    assert msg["From"] == "sender@example.com"
    assert msg["To"] == "reader@example.com"
    assert msg["Subject"] == "Reading batch"
    assert "Chapter 1" in msg.get_content()
