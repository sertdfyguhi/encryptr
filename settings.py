from dataclasses import dataclass, fields, asdict
import json
import os


@dataclass
class AppSettings:
    font_scale: float = 1.0
    copy_files_on_add: bool = False
    secure_delete: bool = True
    auto_lock_inactivity: bool = False
    auto_lock_inactivity_time: int = 60 * 5
    auto_lock_unfocus: bool = False

    @classmethod
    def from_file(cls, file_path: str):
        if not file_path or not os.path.isfile(file_path):
            return cls()

        with open(file_path, "r") as f:
            settings_json = json.load(f)

        valid_fields = (f.name for f in fields(cls))
        return cls(**{k: v for k, v in settings_json.items() if k in valid_fields})

    def save(self, file_path: str):
        with open(file_path, "w") as f:
            json.dump(asdict(self), f, separators=(",", ":"))
