from yt_decktrace.ingest import CaptionChoice, choose_korean_caption


def test_authored_korean_caption_wins() -> None:
    info = {
        "subtitles": {"ko": [{"ext": "vtt"}, {"ext": "json3"}]},
        "automatic_captions": {"ko-orig": [{"ext": "json3"}]},
    }

    assert choose_korean_caption(info) == CaptionChoice("ko", "json3", "authored")


def test_original_korean_automatic_caption_is_selected() -> None:
    info = {
        "subtitles": {},
        "automatic_captions": {"en": [{"ext": "vtt"}], "ko-orig": [{"ext": "json3"}]},
    }

    assert choose_korean_caption(info) == CaptionChoice("ko-orig", "json3", "automatic")
