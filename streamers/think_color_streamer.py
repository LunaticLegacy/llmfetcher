from __future__ import annotations

from .streamer_base import Streamer


class ThinkColorStreamer(Streamer):
    def __call__(self, msg: str) -> bool:
        self.feed(msg)
        return False
