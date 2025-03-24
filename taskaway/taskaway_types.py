import json
from taskaway.constants import ALL_VISIBLE_COLUMNS, DEFAULT_VISIBLE_COLUMNS
from pathlib import Path
from textual.binding import Binding

ColumnDefinitions = list[tuple[str, bool]]


class Config:
    def __init__(self, taskaway_config: Path, column_layout: ColumnDefinitions, theme: str):
        self.taskaway_config: Path = taskaway_config.expanduser()
        self.column_layout: ColumnDefinitions = column_layout
        self.theme: str = theme

    def to_dict(self) -> dict:
        return {
            "column_layout": self.column_layout,
            "theme": self.theme,
        }

    def save_to_json(self):
        with self.taskaway_config.open("w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def default_config(cls, taskaway_config: Path) -> "Config":
        column_layout: ColumnDefinitions = [(x, True) for x in DEFAULT_VISIBLE_COLUMNS]
        for column_definition in ALL_VISIBLE_COLUMNS:
            if not any(column_definition == x for x, _ in column_layout):
                column_layout.append((column_definition, False))

        return cls(
            taskaway_config=taskaway_config,
            column_layout=column_layout,
            theme="gruvbox",
        )

    @classmethod
    def from_dict(cls, taskaway_config: Path, data: dict) -> "Config":
        column_layout = [tuple(item) for item in data["column_layout"]]
        for column_definition in ALL_VISIBLE_COLUMNS:
            if not any(column_definition == x for x, _ in column_layout):
                column_layout.append((column_definition, False))

        column_layout = [(column, visible) for column, visible in column_layout if column in ALL_VISIBLE_COLUMNS]

        return cls(
            taskaway_config=taskaway_config,
            column_layout=column_layout,
            theme=data["theme"],
        )

    @classmethod
    def load_from_json(cls, taskaway_config: Path) -> "Config":
        expanded_path: Path = taskaway_config.expanduser()
        try:
            with expanded_path.open("r") as f:
                data = json.load(f)
        except FileNotFoundError:
            default_config = cls.default_config(taskaway_config=taskaway_config)
            default_config.save_to_json()
            return default_config

        return cls.from_dict(taskaway_config=taskaway_config, data=data)

    def __repr__(self):
        return f"Config(column_layout={self.column_layout}, theme={self.theme})"


class TaskAwayBinding(Binding):
    def __init__(self, category: str, key: str, action: str, description: str) -> None:
        self.category: str = category
        super().__init__(key, action, description, show=False)
