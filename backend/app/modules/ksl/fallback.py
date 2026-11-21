"""Avatar, then rendered video, then captions and icons, then a person."""

LADDER = ("avatar", "video", "captions", "human")


def choose(has_avatar: bool, has_video: bool, has_caption: bool) -> str:
    if has_avatar:
        return "avatar"
    if has_video:
        return "video"
    if has_caption:
        return "captions"
    return "human"


def step_after(failed: str) -> str:
    if failed not in LADDER:
        return "human"
    index = LADDER.index(failed)
    return LADDER[min(index + 1, len(LADDER) - 1)]
