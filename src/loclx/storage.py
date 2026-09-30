"""Session storage, location history retention, and export utilities."""

from __future__ import annotations

import csv
import io
import json
import time
from typing import Any, Optional


class SessionStorage:
    """Manages location history records for authorized sessions."""

    def __init__(self, persistent: bool = False) -> None:
        self.persistent = persistent
        self.history: list[dict[str, Any]] = []

    def add_record(self, record: dict[str, Any]) -> None:
        entry = {
            "timestamp": record.get("timestamp") or time.strftime("%H:%M:%S"),
            "lat": record.get("lat"),
            "lon": record.get("lon"),
            "accuracy": record.get("accuracy"),
            "altitude": record.get("altitude"),
        }
        self.history.append(entry)

    def get_history(self) -> list[dict[str, Any]]:
        return list(self.history)

    def clear_history(self) -> None:
        self.history.clear()

    def export_json(self) -> str:
        return json.dumps(self.history, indent=2)

    def export_csv(self) -> str:
        output = io.StringIO()
        fieldnames = ["timestamp", "lat", "lon", "accuracy", "altitude"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for record in self.history:
            writer.writerow({
                "timestamp": record.get("timestamp", ""),
                "lat": record.get("lat", ""),
                "lon": record.get("lon", ""),
                "accuracy": record.get("accuracy", ""),
                "altitude": record.get("altitude", ""),
            })
        return output.getvalue()
