from __future__ import annotations

import sys
from abc import ABC, abstractmethod

GRAY = "\033[90m"
WHITE = "\033[97m"
RESET = "\033[0m"


class Streamer(ABC):
    START = "<think>"
    END = "</think>"

    def __init__(self) -> None:
        self.in_think = False
        self.buffer = ""
        self.token_counter: int = 0

    @abstractmethod
    def __call__(self, msg: str) -> bool:
        self.feed(msg)
        return False

    def feed(self, msg: str) -> None:
        self.buffer += msg

        while self.buffer:
            marker = self.END if self.in_think else self.START
            idx = self.buffer.find(marker)

            if idx != -1:
                self._emit(self.buffer[:idx])
                self.buffer = self.buffer[idx + len(marker):]
                self.in_think = not self.in_think
                continue

            keep = self._possible_marker_prefix_len(self.buffer, marker)
            if keep == len(self.buffer):
                return

            emit_text = self.buffer[:-keep] if keep > 0 else self.buffer
            self.buffer = self.buffer[-keep:] if keep > 0 else ""
            self._emit(emit_text)

    def finish(self) -> None:
        if self.buffer:
            self.token_counter += 1
            self._emit(self.buffer)
            self.buffer = ""

        sys.stdout.write(RESET + "\n")
        sys.stdout.flush()

    def _emit(self, text: str) -> None:
        self.token_counter += 1

        if not text:
            return

        color = GRAY if self.in_think else WHITE
        sys.stdout.write(color + text + RESET)
        sys.stdout.flush()

    @staticmethod
    def _possible_marker_prefix_len(text: str, marker: str) -> int:
        max_len = min(len(text), len(marker) - 1)

        for n in range(max_len, 0, -1):
            if marker.startswith(text[-n:]):
                return n

        return 0

    def get_tokens(self) -> int:
        return self.token_counter
