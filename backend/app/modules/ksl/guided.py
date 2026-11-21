"""Guided KSL call. Taps are the real path. Recognition is not enabled in this build."""

from __future__ import annotations

MENU = (
    "yes",
    "no",
    "same",
    "better",
    "worse",
    "cant_go",
    "need_interpreter",
    "need_help",
    "repeat",
    "stop",
)
ESCALATE = {"worse", "cant_go", "need_help"}
RECOGNITION_OFF = "Recognition not enabled in this build."


class DisabledRecognizer:
    """The build that ships. It never accepts a guess."""

    def hear(self, label: str, confidence: float) -> str | None:
        del label, confidence
        return None


class SimulatorRecognizer:
    """Wizard-of-Oz stand-in for tests. It reads a label, never video bytes."""

    def hear(self, label: str, confidence: float) -> str | None:
        if confidence < 0.8 or label not in MENU:
            return None
        return label


class GuidedCall:
    def __init__(self) -> None:
        self.phase = "ask"
        self.pending: str | None = None
        self.committed: str | None = None
        self.tasks: list[str] = []
        self.taps_only = True

    def tap(self, choice: str) -> dict:
        return self._offer(choice)

    def recognize(self, recognizer, label: str, confidence: float) -> dict:
        heard = recognizer.hear(label, confidence)
        if heard is None:
            return self._view("repeat", recognition=RECOGNITION_OFF)
        return self._offer(heard)

    def confirm(self, yes: bool) -> dict:
        if self.phase != "confirm" or not self.pending:
            return self._view("repeat", error="nothing_to_confirm")
        if not yes:
            self.pending = None
            self.phase = "ask"
            return self._view("repeat")
        choice = self.pending
        self.pending = None
        self.committed = choice
        if choice in ESCALATE:
            if choice not in self.tasks:
                self.tasks.append(choice)
            self.phase = "handover"
            return self._view("handover")
        self.phase = "done"
        return self._view("done")

    def consent(self, use_camera: bool) -> dict:
        if use_camera:
            self.taps_only = True
            return self._view("consent_taps")
        self.taps_only = True
        self.phase = "ask"
        return self._view("consent_taps")

    def _offer(self, choice: str) -> dict:
        if choice not in MENU:
            return self._view("repeat")
        if choice == "repeat":
            self.phase = "ask"
            return self._view("repeat")
        if choice == "stop":
            self.pending = None
            self.committed = "stop"
            self.phase = "done"
            return self._view("stop")
        self.pending = choice
        self.phase = "confirm"
        return self._view("confirm")

    def _view(self, say: str, error: str | None = None, recognition: str = RECOGNITION_OFF) -> dict:
        return {
            "phase": self.phase,
            "say": say,
            "pending": self.pending,
            "committed": self.committed,
            "tasks": list(self.tasks),
            "taps_only": self.taps_only,
            "recognition": recognition,
            "error": error,
        }
