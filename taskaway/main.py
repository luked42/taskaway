from tasklib import TaskWarrior, Task
from textual.app import App, ComposeResult
from textual.widgets import DataTable

class MainWindow(App):

    def compose(self) -> ComposeResult:
        self.expanded_projects: set[str] = set([''])
        yield DataTable()

    def on_mount(self) -> None:
        self.redraw()
        #self.update_timer = self.set_interval(10, self.redraw)

    def _get_projects(self, tasks: list[Task]) -> set[str]:
        projects: set[str] = set()
        for task in tasks:
            project = task['project']
            if project:
                projects.add(str(project)) 

        return projects

    def _get_parent_project(self, project) -> str:
        if not project:
            return ''
        return '.'.join(project.split('.')[:-1])

    def key_k(self) -> None:
        table = self.query_one(DataTable)
        table.action_cursor_up()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one(DataTable)
        row = table.get_row_at(table.cursor_row)
        description = row[2]
        if description:
            return

        project = row[-1]

        if project in self.expanded_projects:
            self.expanded_projects = {p for p in self.expanded_projects if not p.startswith(project)}
        else:
            self.expanded_projects.add(project)

        self.redraw()
        table.move_cursor(row=table.get_row_index(event.row_key))

    def key_j(self) -> None:
        table = self.query_one(DataTable)
        table.action_cursor_down()

    def _convert_project(self, project: str) -> str:
        if not project:
            return project

        num_periods = project.count('.')
        base_project = '▶ ' if project not in self.expanded_projects else '▼ '
        base_project += project.split('.')[-1]
        return ' ' * (num_periods * 2) + base_project


    def redraw(self) -> None:
        tw = TaskWarrior('~/.task')
        tasks = tw.tasks.pending()
        headers = {
                'project': 20,
                'description': 30,
                'urg': 5,
                'project_hidden': 0,
        }
        task_data = []
        for task in tasks:
            project = task['project']
            if project and project not in self.expanded_projects:
                continue
            task_data.append((None, task['description'], task['urgency'], task['project']))

        table = self.query_one(DataTable)
        table.clear(columns=True)
        for header, width in headers.items():
            table.add_column(header, key=header, width=width)
        for data in task_data:
            table.add_row(*data, key=str(data[0])+str(data[1]))
        table.cursor_type = 'row'
        table.zebra_stripes = True

        projects: set[str] = self._get_projects(tasks)
        for project in projects:
            if self._get_parent_project(project) not in self.expanded_projects:
                continue
            converted_project: str = self._convert_project(project)
            key = project 
            table.add_row(*(converted_project, None, None, project), key=key)
        def sort_by_project_then_description(row_data):
            project, description = row_data
            return (project if project else '', description if description else '')
        table.sort('project_hidden', 'description', key=sort_by_project_then_description)

def start_application() -> None:
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    start_application()
