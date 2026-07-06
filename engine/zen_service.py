"""
ZEN Engine wrapper.

Wraps the `zen-engine` PyPI package (gorules/zen) to provide a clean,
error-isolated interface. The engine instance is lazily created and reused.

Install: pip install zen-engine
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import zen as _zen_lib  # type: ignore[import]
    _ZEN_AVAILABLE = True
    logger.info("zen-engine loaded successfully.")
except ImportError:
    _zen_lib = None  # type: ignore[assignment]
    _ZEN_AVAILABLE = False
    logger.warning(
        "zen-engine not found. Install it with: pip install zen-engine\n"
        "Rule evaluation will be unavailable until it is installed."
    )


class ZenService:
    """
    Thread-safe wrapper around zen.ZenEngine.

    A single instance is sufficient for the lifetime of the application.
    """

    def __init__(self) -> None:
        self._engine: Any = None
        if _ZEN_AVAILABLE:
            try:
                self._engine = _zen_lib.ZenEngine()
            except Exception as exc:
                logger.error("Failed to create ZenEngine instance: %s", exc)

    @property
    def is_available(self) -> bool:
        return self._engine is not None

    def evaluate(self, decision_model: dict, invoice_data: dict) -> dict:
        """
        Evaluate *invoice_data* against *decision_model*.

        Returns a normalised dict::

            {
                "action":      str | None,
                "matchedRule": str | None,
                "raw":         Any,
                "error":       str | None,
            }
        """
        if not self.is_available:
            return {
                "action": None,
                "matchedRule": None,
                "raw": None,
                "error": (
                    "zen-engine is not installed. "
                    "Run: pip install zen-engine"
                ),
            }

        try:
            # create_decision accepts the model as a plain dict
            decision = self._engine.create_decision(decision_model)
            raw = decision.evaluate(invoice_data)

            # Raw is a dict: {"result": {...}, "performance": "..."}
            if isinstance(raw, dict):
                result_data = raw.get("result") or {}
                performance = raw.get("performance")
            else:
                result_data = getattr(raw, "result", {}) or {}
                performance = getattr(raw, "performance", None)

            if not isinstance(result_data, dict):
                result_data = {}

            return {
                "action":      result_data.get("action"),
                "matchedRule": result_data.get("matchedRule"),
                "raw":         raw,
                "performance": performance,
                "error":       None,
            }

        except Exception as exc:
            logger.error("ZEN Engine evaluation error: %s", exc)
            return {
                "action":      None,
                "matchedRule": None,
                "raw":         None,
                "error":       str(exc),
            }


# ── Module-level singleton ─────────────────────────────────────────────────
_service: Optional[ZenService] = None


def get_zen_service() -> ZenService:
    global _service
    if _service is None:
        _service = ZenService()
    return _service
