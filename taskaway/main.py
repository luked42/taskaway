import argparse
import shutil
from pathlib import Path
from os import system
from tasklib import TaskWarrior, Task
from tasklib.backends import TaskWarriorException
from textual import work
from textual.css.query import NoMatches
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import DataTable, Input, Label, Pretty
from textual.widgets._data_table import RowDoesNotExist, CellDoesNotExist, RowKey
from textual.binding import Binding, BindingType
from textual.screen import ModalScreen
from taskaway.column_layout_screen import ColumnLayoutScreen
from typing import Optional, ClassVar
from taskaway.constants import (
    COL_ACTIVE_HIDDEN,
    COL_ANNOTATIONS,
    COL_FULL_PROJECT_HIDDEN,
    COL_SHORT_PROJECT,
    COL_DESCRIPTION_HIDDEN,
    COL_TAGS,
    COL_UUID_HIDDEN,
    HELP_TABLE_ID,
    TASK_PROJECT,
    TASK_TABLE_ID,
    TASK_TAGS,
)
from taskaway.utils import get_all_projects_from_tasks, get_parent_project, get_column_value_for_task
from taskaway.taskaway_types import Config, TaskAwayBinding


class ErrorMessageScreen(ModalScreen):
    def __init__(self, error_msg: str) -> None:
        self.error_msg: str = error_msg
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Pretty(self.error_msg),
            Label("Press any key to continue...", id="error_message"),
        )

    def on_key(self) -> None:
        self.dismiss()


class ConfirmationScreen(ModalScreen[bool]):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "return", "Exit without any action", show=True),
    ]

    def __init__(self, confirmation_question: str) -> None:
        self.confirmation_question: str = confirmation_question
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.confirmation_question, id="command"),
            Input(placeholder="y/n", restrict=r"[yn]", id="input"),
            id="dialog",
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        input_result: str = self.query_one("#input").value
        if input_result == "y":
            self.dismiss(True)
        elif input_result == "n":
            self.dismiss(False)

        self.dismiss(False)

    def action_return(self) -> None:
        self.dismiss("")


class InputCommandScreen(ModalScreen):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "return", "Exit without any action", show=True),
    ]

    def __init__(self, command: str, default_text: str, placeholder_text: str) -> None:
        self.command: str = command
        self.default_text: str = default_text
        self.placeholder_text: str = placeholder_text
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.command, id="command"),
            Input(value=self.default_text, placeholder=self.placeholder_text, select_on_focus=False, id="input"),
            id="dialog",
        )

    def on_mount(self) -> None:
        self.query_one("#input").action_cursor_right()

    def action_return(self) -> None:
        self.dismiss("")

    def on_input_submitted(self) -> None:
        description_input: str = self.query_one("#input").value
        self.dismiss(description_input)


class HelpScreen(ModalScreen):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "return", "Exit help screen", show=False),
        Binding("h", "return", "Exit help screen", show=False),
        Binding("q", "retun", "Quit and save"),
        Binding("j", "cursor_down", "Cursor down"),
        Binding("k", "cursor_up", "Cursor up"),
    ]

    def __init__(self, help_commands: list[TaskAwayBinding]) -> None:
        self.help_commands: list[TaskAwayBinding] = help_commands
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(DataTable(id=HELP_TABLE_ID))

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("Category", key="category")
        table.add_column("Command", key="command")
        table.add_column("Description", key="description")
        for help_command in self.help_commands:
            table.add_row(help_command.category, help_command.key, help_command.description)

        table.cursor_type = "row"
        table.zebra_stripes = True

    def get_table(self) -> DataTable:
        return self.query_one(f"#{HELP_TABLE_ID}")

    def action_return(self) -> None:
        self.dismiss()

    def action_cursor_down(self) -> None:
        table = self.get_table()
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        table = self.get_table()
        table.action_cursor_up()


class MainWindow(App):
    CSS_PATH = "taskaway.tcss"
    HELP = "hello world"
    BINDINGS: ClassVar[list[TaskAwayBinding]] = [
        TaskAwayBinding("Application", "h", "toggle_help", "Toggle help"),
        TaskAwayBinding("Application", "l", "configure_column_layout", "Configure column layout"),
        TaskAwayBinding("Application", "q", "quit", "Quit and save"),
        TaskAwayBinding("Application", "ctrl+t", "change_theme", "Change theme"),
        TaskAwayBinding("Navigation", "G", "cursor_bottom", "Cursor bottom"),
        TaskAwayBinding("Navigation", "g", "cursor_top", "Cursor top"),
        TaskAwayBinding("Navigation", "j", "cursor_down", "Cursor down"),
        TaskAwayBinding("Navigation", "k", "cursor_up", "Cursor up"),
        TaskAwayBinding("Task", "A", "add_annotation", "Add annotation"),
        TaskAwayBinding("Task", "a", "add_task", "Add task"),
        TaskAwayBinding("Task", "b", "toggle_start_stop", "Toggle start stop"),
        TaskAwayBinding("Task", "d", "mark_task_complete", "Mark task complete"),
        TaskAwayBinding("Task", "e", "edit_task", "Edit task"),
        TaskAwayBinding("Task", "m", "modify_task", "Modify task"),
        TaskAwayBinding("Task", "p", "modify_project", "Modify project"),
        TaskAwayBinding("Task", "t", "add_tag", "Add tag to task"),
        TaskAwayBinding("View", "P", "filter_project", "Filter for highlighted project"),
        TaskAwayBinding("View", "T", "filter_tag", "Filter for highlighted tags"),
        TaskAwayBinding("View", "escape", "clear_filters", "Clear filters"),
    ]

    def __init__(self, task_config: Path, taskaway_config: Path, task_command: str) -> None:
        self.tw = TaskWarrior(task_command=task_command, taskrc_location=task_config)
        self.taskaway_config: Path = taskaway_config
        self.config: Config = Config.load_from_json(taskaway_config=self.taskaway_config)
        self.update_project_filter("")
        self.update_tag_filter(tag_filter="")
        super().__init__()

    def get_table(self) -> DataTable:
        return self.query_one(f"#{TASK_TABLE_ID}")

    def update_project_filter(self, project_filter: str) -> None:
        self.project_filter = project_filter.strip()

    def update_tag_filter(self, tag_filter: str) -> None:
        self.tag_filter: list[str] = [x for x in tag_filter.split(",") if x]

    def compose(self) -> ComposeResult:
        self.expanded_projects: set[str] = set([""])
        yield DataTable(id=TASK_TABLE_ID)

    def on_mount(self) -> None:
        self.theme = self.config.theme
        self.redraw()
        self.update_timer = self.set_interval(1.0, self.redraw_if_focused)

    def key_b(self) -> None:
        self.update_timer.pause()

    def is_project_row_highlighted(self) -> bool:
        table = self.get_table()
        try:
            row = table.get_row_at(table.cursor_row)
        except RowDoesNotExist:
            return False

        uuid_column_idx: int = table.get_column_index(COL_UUID_HIDDEN)
        return row[uuid_column_idx] is None

    def is_task_row_highlighted(self) -> bool:
        table = self.get_table()
        try:
            row = table.get_row_at(table.cursor_row)
        except RowDoesNotExist:
            return False

        uuid_column_idx: int = table.get_column_index(COL_UUID_HIDDEN)
        return row[uuid_column_idx] is not None

    def get_highlighted_row_full_project(self) -> Optional[str]:
        table = self.get_table()
        try:
            row = table.get_row_at(table.cursor_row)
            project_hidden_idx: int = table.get_column_index(COL_FULL_PROJECT_HIDDEN)
            return row[project_hidden_idx]
        except RowDoesNotExist:
            return None

    def get_highlighted_row_key(self) -> Optional[RowKey]:
        table = self.get_table()
        try:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            return row_key
        except CellDoesNotExist:
            return None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.get_table()
        row = table.get_row_at(table.cursor_row)

        if not self.is_project_row_highlighted():
            return

        row_key: Optional[str] = self.get_highlighted_row_key()
        if not row_key:
            return

        column_index: int = table.get_column_index(COL_FULL_PROJECT_HIDDEN)
        project = row[column_index]

        if project in self.expanded_projects:
            self.expanded_projects = {p for p in self.expanded_projects if not p.startswith(project)}
        else:
            self.expanded_projects.add(project)

        self.call_after_refresh(self.redraw)

    def action_clear_filters(self) -> None:
        self.update_project_filter("")
        self.update_tag_filter(tag_filter="")
        self.call_after_refresh(self.redraw)

    def action_cursor_up(self) -> None:
        table = self.get_table()
        table.action_cursor_up()

    def action_cursor_down(self) -> None:
        table = self.get_table()
        table.action_cursor_down()

    def action_cursor_top(self) -> None:
        table = self.get_table()
        table.action_scroll_top()

    def action_cursor_bottom(self) -> None:
        table = self.get_table()
        table.action_scroll_bottom()

    @work
    async def action_configure_column_layout(self) -> None:
        column_layout = await self.push_screen_wait(ColumnLayoutScreen(self.config.column_layout))
        self.config.column_layout = column_layout
        self.config.save_to_json()
        self.call_after_refresh(self.redraw)

    @work
    async def action_mark_task_complete(self) -> None:
        if not self.is_task_row_highlighted():
            return

        table = self.get_table()
        row = table.get_row_at(table.cursor_row)
        uuid_column_idx: int = table.get_column_index(COL_UUID_HIDDEN)

        if not await self.push_screen_wait(ConfirmationScreen(confirmation_question="Mark task done?")):
            return

        task_uuid: str = row[uuid_column_idx]
        task: Task = self.tw.get_task(task_uuid)
        task.done()
        task.save()
        table.action_cursor_up()
        self.call_after_refresh(self.redraw)

    @work
    async def action_add_tag(self) -> None:
        if not self.is_task_row_highlighted():
            return

        table = self.get_table()

        tags_command = await self.push_screen_wait(
            InputCommandScreen(command="AddTags", default_text="", placeholder_text="space separated tags")
        )
        if tags_command == "":
            return

        row = table.get_row_at(table.cursor_row)
        uuid_column_idx: int = table.get_column_index(COL_UUID_HIDDEN)
        task_uuid: str = row[uuid_column_idx]
        self.tw.execute_command([task_uuid, "modify"] + [f"+{x}" for x in tags_command.split(" ")])
        self.call_after_refresh(self.redraw)

    @work
    async def action_modify_project(self) -> None:
        if not self.is_task_row_highlighted():
            return

        highlighted_project: Optional[str] = self.get_highlighted_row_full_project()
        default_project: str = f"project:{highlighted_project}" if highlighted_project is not None else "project:"

        table = self.get_table()

        modify_command = await self.push_screen_wait(
            InputCommandScreen(
                command="Modify", default_text=default_project, placeholder_text="task warrior modify syntax"
            )
        )
        if modify_command == "":
            return

        row = table.get_row_at(table.cursor_row)
        uuid_column_idx: int = table.get_column_index(COL_UUID_HIDDEN)
        task_uuid: str = row[uuid_column_idx]
        self.tw.execute_command([task_uuid, "modify"] + modify_command.split(" "))
        self.call_after_refresh(self.redraw)

    @work
    async def action_modify_task(self) -> None:
        if not self.is_task_row_highlighted():
            return

        table = self.get_table()

        modify_command = await self.push_screen_wait(
            InputCommandScreen(command="Modify", default_text="", placeholder_text="task warrior modify syntax")
        )
        if modify_command == "":
            return

        row = table.get_row_at(table.cursor_row)
        uuid_column_idx: int = table.get_column_index(COL_UUID_HIDDEN)
        task_uuid: str = row[uuid_column_idx]
        self.tw.execute_command([task_uuid, "modify"] + modify_command.split(" "))
        self.call_after_refresh(self.redraw)

    @work
    async def action_add_task(self) -> None:
        highlighted_project: Optional[str] = self.get_highlighted_row_full_project()
        default_project: str = f"project:{highlighted_project} " if highlighted_project is not None else ""

        add_command = await self.push_screen_wait(
            InputCommandScreen(command="AddTask", default_text=default_project, placeholder_text="")
        )
        if add_command == "":
            return

        try:
            self.tw.execute_command(["add"] + add_command.split(" "))
        except TaskWarriorException as twe:
            await self.push_screen_wait(ErrorMessageScreen(error_msg=twe))
        self.call_after_refresh(self.redraw)

    @work
    async def action_add_annotation(self) -> None:
        if not self.is_task_row_highlighted():
            return

        table = self.get_table()

        annotation_command = await self.push_screen_wait(
            InputCommandScreen(command="Annotation", default_text="", placeholder_text="")
        )
        if annotation_command == "":
            return

        row = table.get_row_at(table.cursor_row)
        uuid_column_idx: int = table.get_column_index(COL_UUID_HIDDEN)
        task_uuid: str = row[uuid_column_idx]
        self.tw.execute_command([task_uuid, "annotate"] + annotation_command.split(" "))
        self.call_after_refresh(self.redraw)

    @work
    async def action_edit_task(self) -> None:
        if not self.is_task_row_highlighted():
            return

        table = self.get_table()
        row = table.get_row_at(table.cursor_row)
        uuid_column_idx: int = table.get_column_index(COL_UUID_HIDDEN)
        task_uuid: str = row[uuid_column_idx]
        with self.suspend():
            system(f"task {task_uuid} edit")
        self.call_after_refresh(self.redraw)

    @work
    async def action_toggle_start_stop(self) -> None:
        if not self.is_task_row_highlighted():
            return

        table = self.get_table()
        row = table.get_row_at(table.cursor_row)
        uuid_column_idx: int = table.get_column_index(COL_UUID_HIDDEN)
        task_uuid: str = row[uuid_column_idx]

        task: Task = self.tw.get_task(task_uuid)
        if task.active:
            task.stop()
        else:
            task.start()
        task.save()
        self.call_after_refresh(self.redraw)

    @work
    async def action_toggle_help(self) -> None:
        try:
            await self.push_screen_wait(HelpScreen(self.BINDINGS))
        except NoMatches:
            pass

    @work
    async def action_filter_project(self) -> None:
        row_key = self.get_highlighted_row_key()
        if row_key is None:
            return

        table = self.get_table()
        if not self.is_task_row_highlighted():
            return

        table = self.get_table()
        row = table.get_row_at(table.cursor_row)

        project_hidden_idx: int = table.get_column_index(COL_FULL_PROJECT_HIDDEN)
        project: Optional[str] = row[project_hidden_idx]

        if project is None:
            return

        self.update_project_filter(project_filter=project)
        self.call_after_refresh(self.redraw)

    @work
    async def action_filter_tag(self) -> None:
        row_key = self.get_highlighted_row_key()
        if row_key is None:
            return

        # Filter for tag
        table = self.get_table()
        row = table.get_row_at(table.cursor_row)

        tags_idx: int = table.get_column_index(COL_TAGS)
        tags: Optional[str] = row[tags_idx]

        if tags is None:
            return

        self.update_tag_filter(tag_filter=tags)
        self.call_after_refresh(self.redraw)

    @work
    async def action_quit(self) -> None:
        if not await self.push_screen_wait(ConfirmationScreen(confirmation_question="Quit?")):
            return
        self.exit()

    def watch_theme(self) -> None:
        if self.config.theme == self.theme:
            return

        self.config.theme = self.theme
        self.config.save_to_json()

    def action_change_theme(self) -> None:
        self.search_themes()

    def convert_project(self, project: str) -> str:
        if not project:
            return project

        num_periods = project.count(".")
        base_project = "▶ " if project not in self.expanded_projects else "▼ "
        base_project += project.split(".")[-1]
        return " " * (num_periods * 2) + base_project

    def redraw_if_focused(self) -> None:
        try:
            table = self.get_table()
            if not table.has_focus:
                return
            self.redraw()
        except NoMatches:
            return

    def redraw_columns(self) -> None:
        table = self.get_table()
        columns = [column.value for column in table.columns]
        for column in columns:
            table.remove_column(column)

        headers = (
            {
                COL_SHORT_PROJECT: None,
            }
            | {col_name: None for col_name, show_col in self.config.column_layout if show_col}
            | {
                COL_DESCRIPTION_HIDDEN: 0,
                COL_ACTIVE_HIDDEN: 0,
                COL_FULL_PROJECT_HIDDEN: 0,
                COL_UUID_HIDDEN: 0,
            }
        )

        for header, width in headers.items():
            table.add_column(header, key=header, width=width)

    def redraw(self) -> None:
        self.redraw_columns()
        table = self.get_table()
        row_key = self.get_highlighted_row_key()

        tasks = self.tw.tasks.pending()
        task_data = []
        tag_filter_projects: set[str] = set()
        for task in tasks:
            project = task[TASK_PROJECT]
            tags = [x for x in task[TASK_TAGS] if x]
            if self.tag_filter and (not tags or not any(tag in self.tag_filter for tag in tags)):
                continue

            if self.tag_filter and project is not None:
                tag_filter_projects.add(project)

            if project and project not in self.expanded_projects and not task.active:
                continue

            if self.project_filter and (project is None or not project.startswith(self.project_filter)):
                continue

            data = []
            height: int = 1
            for column in table.columns:
                column_value: str = get_column_value_for_task(task, column.value)
                # Hack for now, auto height not working as expected in data table
                if column == COL_ANNOTATIONS:
                    height = column_value.count("\n") + 1
                if column == COL_SHORT_PROJECT and task.active:
                    data.append(project)
                else:
                    data.append(get_column_value_for_task(task, column.value))
            task_data.append((data, height))

        table.clear()
        for data, height in task_data:
            table.add_row(*data, height=height, key=str(data[-1]) + str(data[-2]))
        table.cursor_type = "row"
        table.zebra_stripes = True

        projects: set[str] = get_all_projects_from_tasks(tasks)
        for project in projects:
            if self.project_filter and not project.startswith(self.project_filter):
                continue

            if self.tag_filter and not any(
                tag_filter_project.startswith(project) for tag_filter_project in tag_filter_projects
            ):
                continue

            if get_parent_project(project) not in self.expanded_projects:
                continue

            converted_project: str = self.convert_project(project)
            key = project
            data = []
            for column in table.columns:
                if column.value == COL_SHORT_PROJECT:
                    data.append(converted_project)
                elif column.value == COL_FULL_PROJECT_HIDDEN:
                    data.append(project)
                elif column.value == COL_ACTIVE_HIDDEN:
                    data.append(999999999)
                else:
                    data.append(None)
            table.add_row(*data, key=key)

        def sort_by_project_then_description(row_data):
            active, project, description = row_data
            return (active if active else 999999999999, project if project else "", description if description else "")

        table.sort(
            COL_ACTIVE_HIDDEN, COL_FULL_PROJECT_HIDDEN, COL_DESCRIPTION_HIDDEN, key=sort_by_project_then_description
        )

        try:
            table.move_cursor(row=table.get_row_index(row_key))
        except RowDoesNotExist:
            return


def start_application() -> None:
    parser = argparse.ArgumentParser(
        prog="taskaway",
        description="terminal user interface for task warrior",
    )
    parser.add_argument("--task_config", required=False, default="~/.task", help="path for task config file to use")
    parser.add_argument(
        "--taskaway_config", required=False, default="~/.taskaway.json", help="path for taskaway config file to use"
    )
    parser.add_argument("--task_command", required=False, default="task", help="command to run task warrior task")

    args = parser.parse_args()
    task_command: str = args.task_command
    if shutil.which(task_command) is None:
        print(
            f"The task command '{task_command}' does not exist. "
            f"Install task warrior following https://taskwarrior.org/download/#quick-setup."
        )
        exit(1)

    app = MainWindow(
        task_config=Path(args.task_config), taskaway_config=Path(args.taskaway_config), task_command=task_command
    )
    app.run()


if __name__ == "__main__":
    start_application()
