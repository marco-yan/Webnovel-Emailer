from src.scraper import Chapter, Novel
from src.web_service import build_plan, normalize_recipients


def _novel(total: int = 20) -> Novel:
    return Novel(
        title="Example Novel",
        source_url="https://example.com/novel/",
        chapters=[
            Chapter(title=f"Chapter {i}", url=f"https://example.com/novel/chapter/{i}/", number=i)
            for i in range(1, total + 1)
        ],
    )


def test_range_is_inclusive():
    plan = build_plan(_novel(500), 30, 400, 10)
    assert len(plan.chapters) == 371
    assert len(plan.batches) == 38
    assert plan.batches[0][0].number == 30
    assert plan.batches[-1][-1].number == 400


def test_recipient_cleanup():
    recipients = normalize_recipients("A@example.com, b@example.com\na@example.com")
    assert recipients == ["A@example.com", "b@example.com"]
