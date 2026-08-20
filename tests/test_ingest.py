import pytest

from yt_decktrace.ingest import CaptionChoice, choose_caption, choose_korean_caption


def test_authored_korean_caption_wins() -> None:
    info = {
        "subtitles": {"ko": [{"ext": "vtt"}, {"ext": "json3"}]},
        "automatic_captions": {"ko-orig": [{"ext": "json3"}]},
    }

    assert choose_korean_caption(info) == CaptionChoice("ko", "json3", "authored", False)


def test_original_korean_automatic_caption_is_selected() -> None:
    info = {
        "subtitles": {},
        "automatic_captions": {"en": [{"ext": "vtt"}], "ko-orig": [{"ext": "json3"}]},
    }

    assert choose_korean_caption(info) == CaptionChoice("ko-orig", "json3", "automatic", True)


def test_original_automatic_caption_wins_over_youtube_translations() -> None:
    info = {
        "language": "en-US",
        "subtitles": {"live_chat": [{"ext": "json"}]},
        "automatic_captions": {
            "ko": [{"ext": "json3"}],
            "en": [{"ext": "json3"}],
            "en-orig": [{"ext": "vtt"}, {"ext": "json3"}],
        },
    }

    assert choose_caption(info) == CaptionChoice("en-orig", "json3", "automatic", True)


def test_authored_original_language_is_preferred() -> None:
    info = {
        "language": "en-US",
        "subtitles": {
            "ko": [{"ext": "json3"}],
            "en-US": [{"ext": "vtt"}],
        },
        "automatic_captions": {"en-orig": [{"ext": "json3"}]},
    }

    assert choose_caption(info, "original") == CaptionChoice(
        "en-US", "vtt", "authored", True
    )


def test_explicit_translation_language_is_flagged_as_non_original() -> None:
    info = {
        "language": "en-US",
        "subtitles": {},
        "automatic_captions": {
            "en-orig": [{"ext": "json3"}],
            "ko": [{"ext": "json3"}],
        },
    }

    assert choose_caption(info, "ko") == CaptionChoice("ko", "json3", "automatic", False)


def test_rejects_unknown_caption_language() -> None:
    with pytest.raises(ValueError, match="original, ko, en"):
        choose_caption({}, "fr")
