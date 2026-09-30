"""Session storage, location history retention, and export utilities."""

from __future__ import annotations

import csv
import io
import json
import os
import time
from typing import Any, Optional

DEFAULT_MAX_HISTORY = 500


class SessionStorage:
    """Manages location history records for authorized sessions."""

    def __init__(self, persistent: bool = False, max_history: Optional[int] = None) -> None:
        self.persistent = persistent
        if max_history is not None:
            self.max_history = max_history
        else:
            try:
                self.max_history = int(os.environ.get("LOCLX_MAX_HISTORY", DEFAULT_MAX_HISTORY))
            except Exception:
                self.max_history = DEFAULT_MAX_HISTORY
        self.history: list[dict[str, Any]] = []

    def add_record(self, record: dict[str, Any]) -> None:
        entry = {
            "timestamp": record.get("timestamp") or time.strftime("%H:%M:%S"),
            "lat": record.get("lat"),
            "lon": record.get("lon"),
            "accuracy": record.get("accuracy"),
            "altitude": record.get("altitude"),
            "heading": record.get("heading"),
            "speed": record.get("speed"),
        }
        self.history.append(entry)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_history(self) -> list[dict[str, Any]]:
        return list(self.history)

    def clear_history(self) -> None:
        self.history.clear()

    def export_json(self) -> str:
        return json.dumps(self.history, indent=2)

    def export_csv(self) -> str:
        output = io.StringIO()
        fieldnames = ["timestamp", "lat", "lon", "accuracy", "altitude", "heading", "speed"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for record in self.history:
            writer.writerow({
                "timestamp": record.get("timestamp", ""),
                "lat": record.get("lat", ""),
                "lon": record.get("lon", ""),
                "accuracy": record.get("accuracy", ""),
                "altitude": record.get("altitude", ""),
                "heading": record.get("heading", ""),
                "speed": record.get("speed", ""),
            })
        return output.getvalue()
