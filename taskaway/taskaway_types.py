import json
from constants import ALL_VISIBLE_COLUMNS, DEFAULT_VISIBLE_COLUMNS
from pathlib import Path

ColumnDefinitions = list[tuple[str, bool]]


class Config:
    def __init__(self, column_layout: ColumnDefinitions, task_file: str, theme: str):
        self.column_layout = column_layout
        self.task_file = task_file
        self.theme = theme

    def to_dict(self) -> dict:
        return {
            "column_layout": self.column_layout,
            "task_file": self.task_file,
            "theme": self.theme,
        }

    def save_to_json(self, file_path: str):
        path: Path = Path(file_path)
        expanded_path: Path = path.expanduser()
        with expanded_path.open("w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def default_config(cls) -> "Config":
        column_layout: ColumnDefinitions = [(x, True) for x in DEFAULT_VISIBLE_COLUMNS]
        for column_definition in ALL_VISIBLE_COLUMNS:
            if not any(column_definition == x for x, _ in column_layout):
                column_layout.append((column_definition, False))

        return cls(
            column_layout=column_layout,
            task_file="~/.taskrc",
            theme="gruvbox",
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        column_layout = [tuple(item) for item in data["column_layout"]]
        for column_definition in ALL_VISIBLE_COLUMNS:
            if not any(column_definition == x for x, _ in column_layout):
                column_layout.append((column_definition, False))

        column_layout = [(column, visible) for column, visible in column_layout if column in ALL_VISIBLE_COLUMNS]

        return cls(
            column_layout=column_layout,
            task_file=data["task_file"],
            theme=data["theme"],
        )

    @classmethod
    def load_from_json(cls, file_path: str) -> "Config":
        path: Path = Path(file_path)
        expanded_path: Path = path.expanduser()
        try:
            with expanded_path.open("r") as f:
                data = json.load(f)
        except FileNotFoundError:
            default_config = cls.default_config()
            default_config.save_to_json(file_path=file_path)
            return default_config

        return cls.from_dict(data)

    def __repr__(self):
        return f"Config(column_layout={self.column_layout}, task_file={self.task_file}, theme={self.theme})"
