from tasklib import TaskWarrior, Task
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import DataTable, Input, Label
from textual.widgets._data_table import RowDoesNotExist, CellDoesNotExist
from textual.screen import ModalScreen
from typing import Callable, Optional

from datetime import datetime, timezone, timedelta
from taskaway.constants import COMMAND_INPUT_ID, TASK_TABLE_ID

def get_representation(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f'{total_seconds}s'

    total_minutes = int(total_seconds / 60)
    if total_minutes < 60:
        return f'{total_minutes}m'

    total_hours = int(total_minutes / 60)
    if total_hours < 24:
        return f'{total_hours}h'

    total_days = int(total_hours / 24)
    if total_days < 365:
        return f'{total_days}d'

    return f'{int(total_days/365)}y'

class InputCommandScreen(ModalScreen):
    def __init__(self, command: str, default_text: str, placeholder_text: str) -> None:
        self.command: str = command
        self.default_text: str = default_text
        self.placeholder_text: str = placeholder_text
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.command, id="command"),
            Input(value=self.default_text, placeholder=self.placeholder_text, select_on_focus=False, id='input'),
            id="dialog",
        )

    def on_mount(self) -> None:
        self.query_one('#input').action_cursor_right()

    def key_escape(self) -> None:
        self.dismiss("")

    def key_enter(self) -> None:
        description_input: str = self.query_one('#input').value
        self.dismiss(description_input)

class CommandHandler():
    def __init__(self, task_warrior_backend: TaskWarrior, project_filter_updater: Callable) -> None:
        self.task_warrior_backend = task_warrior_backend
        self.project_filter_updater = project_filter_updater

    def handle_command(self, command: str) -> None:
        command_type, command_value = command.split(":", 1)
        print(f"Handling command {command}, {command_type=}, {command=}")
        if command_type == 'Add':
            print("Handling add command")
            self.handle_add(command_value)
        if command_type == 'Filter':
            print("Handling project filter command")
            self.handle_project_filter(command_value)


    def handle_add(self, command: str) -> None:
        fields: list[str] = command.split(' ')
        project_field_idx: Optional[int] = next((index for index, field in enumerate(fields) if 'project:' in field), None)
        project: Optional[str] = None
        if project_field_idx is not None:
            project = fields[project_field_idx].split(":")[-1]
            del fields[project_field_idx]

        fields = [field for field in fields if field != '']
        description: str = ' '.join(fields)
        task: Task = Task(backend=self.task_warrior_backend, project=project, description=description)
        self.task_warrior_backend.save_task(task)
        return f"{task['uuid']}{description}"

    def handle_add_tag(self, task_uuid, tags: str) -> None:
        task: Task = self.task_warrior_backend.get_task(task_uuid)
        for tag in tags.split(' '):
            if not tag:
                continue
            task['tags'].add(tag)
        task.save()
        self.task_warrior_backend.save_task(task)
        return f"{task['uuid']}{task['description']}"

    def handle_project_filter(self, command: str) -> None:
        self.project_filter_updater(command)

class MainWindow(App):
    CSS_PATH = "taskaway.tcss"
    def __init__(self) -> None:
        self.tw = TaskWarrior('~/.task')
        self.update_project_filter('')
        self.update_tag_filter(tag_filter='')
        self.command_handler: CommandHandler = CommandHandler(self.tw, self.update_project_filter)
        super().__init__()

    def update_project_filter(self, project_filter: str) -> None:
        self.project_filter = project_filter.strip()

    def update_tag_filter(self, tag_filter: str) -> None:
        self.tag_filter: list[str] = [x for x in tag_filter.split(',') if x]

    def compose(self) -> ComposeResult:
        self.expanded_projects: set[str] = set([''])
        yield DataTable(id=TASK_TABLE_ID)

    def on_mount(self) -> None:
        self.theme = 'gruvbox'
        headers = {
                'project': None,
                'description': None,
                'urg': None,
                'age': None,
                'tags': None,
                'project_hidden': 0,
                'task_uuid_hidden': 0,
        }
        table = self.query_one(DataTable)
        for header, width in headers.items():
            table.add_column(header, key=header, width=width)
        self.redraw()

    def _get_projects(self, tasks: list[Task]) -> set[str]:
        projects: set[str] = set()
        for task in tasks:
            task_project: str = task['project']
            project = str(task_project) if task_project else ''

            while project:
                projects.add(project)

                last_dot: int = project.rfind('.')
                if last_dot == -1:
                    break

                project = project[0:last_dot]
        return projects

    def _get_parent_project(self, project) -> str:
        if not project:
            return ''
        return '.'.join(project.split('.')[:-1])

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.command_handler.handle_command(event.value)
        self.query_one(f'#{COMMAND_INPUT_ID}').value = ''
        self.redraw()

        table: Input = self.query_one(f'#{TASK_TABLE_ID}')
        table.focus()

    def key_escape(self) -> None:
        table: Input = self.query_one(f'#{TASK_TABLE_ID}')
        if table.has_focus and (self.project_filter or self.tag_filter):
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            self.update_project_filter('')
            self.update_tag_filter(tag_filter='')
            self.redraw()
            table.move_cursor(row=table.get_row_index(row_key))

    def key_k(self) -> None:
        table = self.query_one(DataTable)
        table.action_cursor_up()

    def is_project_row_selected(self) -> bool:
        table = self.query_one(DataTable)
        try:
            row = table.get_row_at(table.cursor_row)
        except RowDoesNotExist:
            return False

        uuid_column_idx: int = table.get_column_index('task_uuid_hidden')
        return row[uuid_column_idx] is None

    def is_task_row_selected(self) -> bool:
        table = self.query_one(DataTable)
        try:
            row = table.get_row_at(table.cursor_row)
        except RowDoesNotExist:
            return False

        uuid_column_idx: int = table.get_column_index('task_uuid_hidden')
        return row[uuid_column_idx] is not None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one(DataTable)
        row = table.get_row_at(table.cursor_row)

        if not self.is_project_row_selected():
            return

        row_key: Optional[str] = self.get_selected_row_key()
        if not row_key:
            return

        column_index: int = table.get_column_index("project_hidden")
        project = row[column_index]

        if project in self.expanded_projects:
            self.expanded_projects = {p for p in self.expanded_projects if not p.startswith(project)}
        else:
            self.expanded_projects.add(project)

        self.redraw()
        table.move_cursor(row=table.get_row_index(row_key))

    def key_j(self) -> None:
        table = self.query_one(DataTable)
        table.action_cursor_down()

    def key_d(self) -> None:
        if not self.is_task_row_selected():
            return

        table = self.query_one(DataTable)
        row = table.get_row_at(table.cursor_row)
        uuid_column_idx: int = table.get_column_index('task_uuid_hidden')
        if row[uuid_column_idx] is None:
            return

        task_uuid: str = row[uuid_column_idx]
        task: Task = self.tw.get_task(task_uuid)
        task.done()
        task.save()
        table.action_cursor_up()
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        self.redraw()
        try:
            table.move_cursor(row=table.get_row_index(row_key))
        except Exception:
            pass

    def get_selected_row_project(self) -> Optional[str]:
        table = self.query_one(DataTable)
        try:
            row = table.get_row_at(table.cursor_row)
            project_hidden_idx: int = table.get_column_index('project_hidden')
            return row[project_hidden_idx]
        except RowDoesNotExist:
            return None

    def get_selected_row_key(self) -> Optional[str]:
        table = self.query_one(DataTable)
        try:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            return row_key
        except CellDoesNotExist:
            return None

    @work
    async def key_t(self) -> None:
        if not self.is_task_row_selected():
            return
        row_key: Optional[str] = self.get_selected_row_key()
        if not row_key:
            return

        table = self.query_one(DataTable)

        tags_command = await self.push_screen_wait(InputCommandScreen(command="AddTags", default_text='', placeholder_text='space separated tags'))
        if tags_command == '':
            return

        row = table.get_row_at(table.cursor_row)
        uuid_column_idx: int = table.get_column_index('task_uuid_hidden')
        task_uuid: str = row[uuid_column_idx]
        self.command_handler.handle_add_tag(task_uuid, tags_command)
        self.redraw()

    @work
    async def key_a(self) -> None:
        table = self.query_one(DataTable)
        selected_project: Optional[str] = self.get_selected_row_project()
        default_project: str = f'project:{selected_project} ' if selected_project is not None else ''

        previous_row_key: Optional[str] = self.get_selected_row_key()

        add_command = await self.push_screen_wait(InputCommandScreen(command="AddTask", default_text=default_project, placeholder_text=''))
        if add_command == '':
            return

        new_row_key: str = self.command_handler.handle_add(add_command)
        self.redraw()

        if previous_row_key is None:
            # Empty data table defaults to first row
            return

        try:
            table.move_cursor(row=table.get_row_index(new_row_key))
        except RowDoesNotExist:
            # New task was created but row is not expanded
            table.move_cursor(row=table.get_row_index(previous_row_key))

    @work
    async def key_f(self) -> None:
        row_key = self.get_selected_row_key()
        if row_key is None:
            return

        table = self.query_one(DataTable)
        row = table.get_row_at(table.cursor_row)

        project_hidden_idx: int = table.get_column_index('project_hidden')
        project: Optional[str] = row[project_hidden_idx]

        if project is None:
            return

        self.update_project_filter(project_filter=project)
        self.redraw()
        table.move_cursor(row=table.get_row_index(row_key))

    @work
    async def key_upper_f(self) -> None:
        row_key = self.get_selected_row_key()
        if row_key is None:
            return

        # Filter for tag
        table = self.query_one(DataTable)
        row = table.get_row_at(table.cursor_row)

        tags_idx: int = table.get_column_index('tags')
        tags: Optional[str] = row[tags_idx]

        if tags is None:
            return

        self.update_tag_filter(tag_filter=tags)
        self.redraw()
        table.move_cursor(row=table.get_row_index(row_key))

    def _convert_project(self, project: str) -> str:
        if not project:
            return project

        num_periods = project.count('.')
        base_project = '▶ ' if project not in self.expanded_projects else '▼ '
        base_project += project.split('.')[-1]
        return ' ' * (num_periods * 2) + base_project

    def redraw(self) -> None:
        tasks = self.tw.tasks.pending()
        task_data = []
        tag_filter_projects: set[str] = set() 
        for task in tasks:
            project = task['project']
            tags = [x for x in task['tags'] if x]
            if self.tag_filter and (not tags or not any(tag in self.tag_filter for tag in tags)):
                continue

            if self.tag_filter and project is not None:
                tag_filter_projects.add(project)

            if project and project not in self.expanded_projects:
                continue

            if self.project_filter and (project is None or not project.startswith(self.project_filter)):
                continue

            age = get_representation(datetime.now(tz=timezone.utc) - task['entry'])
            tags = ','.join(task['tags'])
            task_data.append((None, task['description'], task['urgency'], age, tags, task['project'], task['uuid']))

        table = self.query_one(DataTable)
        table.clear()
        for data in task_data:
            table.add_row(*data, key=str(data[-1])+str(data[1]))
        table.cursor_type = 'row'
        table.zebra_stripes = True

        projects: set[str] = self._get_projects(tasks)
        for project in projects:
            if self.project_filter and not project.startswith(self.project_filter):
                continue

            if self.tag_filter and not any(tag_filter_project.startswith(project) for tag_filter_project in tag_filter_projects):
                continue

            if self._get_parent_project(project) not in self.expanded_projects:
                continue

            converted_project: str = self._convert_project(project)
            key = project
            table.add_row(*(converted_project, None, None, None, None, project, None), key=key)

        def sort_by_project_then_description(row_data):
            project, description = row_data
            return (project if project else '', description if description else '')

        table.sort('project_hidden', 'description', key=sort_by_project_then_description)

def start_application() -> None:
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    start_application()
