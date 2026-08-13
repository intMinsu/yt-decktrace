from yt_decktrace.utils import format_timestamp, youtube_timestamp_url


def test_timestamp_helpers() -> None:
    assert format_timestamp(3723.9) == "01:02:03"
    assert youtube_timestamp_url("https://youtu.be/example", 65.9) == (
        "https://youtu.be/example?t=65s"
    )
    assert youtube_timestamp_url("https://youtube.com/watch?v=x&t=1s", 20) == (
        "https://youtube.com/watch?v=x&t=20s"
    )
