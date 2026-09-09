from app.utils.youtube import extract_video_id


def test_extract_watch_url():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_short_url():
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_shorts_url():
    assert extract_video_id("https://www.youtube.com/shorts/abc123XYZ_9") == "abc123XYZ_9"
