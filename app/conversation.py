from typing import Dict, Any, Tuple

from .storage import Storage


class ConversationManager:
    def __init__(self, storage: Storage, scheduler) -> None:
        self.storage = storage
        self.scheduler = scheduler

    def handle(self, user_id: str, message: str, payload: Dict[str, Any] | None) -> Dict[str, Any]:
        # Extremely simplified state machine, stored per user in prompts.json extras (avoid separate file for brevity)
        state = self._get_state(user_id)
        if state == "start":
            self._set_state(user_id, "awaiting_platform")
            return {"reply": "Welcome! Which platform credentials would you like to add? (instagram/twitter/linkedin)"}
        if state == "awaiting_platform":
            platform = message.strip().lower()
            self._set_state(user_id, f"awaiting_credentials:{platform}")
            return {"reply": f"Please provide {platform} credentials as JSON."}
        if state.startswith("awaiting_credentials:"):
            platform = state.split(":", 1)[1]
            try:
                import json
                creds = json.loads(message)
            except Exception:
                return {"reply": "Invalid JSON. Try again."}
            self.storage.save_credentials(user_id, platform, creds)
            self._set_state(user_id, "awaiting_ad")
            return {"reply": "Credentials saved. Tell me about your product/service (description, tone, audience)."}
        if state == "awaiting_ad":
            # naive parse: split by semicolons
            parts = [p.strip() for p in message.split(";")]
            product = parts[0] if len(parts) > 0 else message
            tone = parts[1] if len(parts) > 1 else "persuasive"
            audience = parts[2] if len(parts) > 2 else "general audience"
            self._set_state(user_id, f"confirm:{product}|{tone}|{audience}")
            return {"reply": f"Got it. Post daily at 12 AM? Reply yes to confirm or provide HH:MM TZ."}
        if state.startswith("confirm:"):
            _, rest = state.split(":", 1)
            product, tone, audience = rest.split("|")
            msg = message.strip().lower()
            if msg.startswith("yes"):
                self.storage.save_schedule(user_id, 0, 0, "UTC")
                # schedule immediately
                try:
                    self.scheduler.schedule_user(user_id)
                except Exception:
                    pass
                self._set_state(user_id, "done")
                return {"reply": "All set! Daily posts at 00:00 UTC will start."}
            try:
                time_part, tz = message.split()
                hour, minute = [int(x) for x in time_part.split(":")]
                self.storage.save_schedule(user_id, hour, minute, tz)
                try:
                    self.scheduler.schedule_user(user_id)
                except Exception:
                    pass
                self._set_state(user_id, "done")
                return {"reply": f"Scheduled daily posts at {hour:02d}:{minute:02d} {tz}."}
            except Exception:
                return {"reply": "Could not parse time. Reply yes or 'HH:MM TZ' (e.g., 09:30 America/New_York)."}
        return {"reply": "Say 'start' to begin."}

    def _get_state(self, user_id: str) -> str:
        # Store in a lightweight file
        from pathlib import Path
        import json
        from .config import settings
        users_dir = Path(settings.data_dir) / "users" / user_id
        users_dir.mkdir(parents=True, exist_ok=True)
        file = users_dir / "state.json"
        if not file.exists():
            return "start"
        try:
            obj = json.loads(file.read_text())
            return obj.get("state", "start")
        except Exception:
            return "start"

    def _set_state(self, user_id: str, state: str) -> None:
        from pathlib import Path
        import json
        from .config import settings
        users_dir = Path(settings.data_dir) / "users" / user_id
        users_dir.mkdir(parents=True, exist_ok=True)
        file = users_dir / "state.json"
        file.write_text(json.dumps({"state": state}, indent=2))
