from textual import work
from textual.widgets import SelectionList, Label
from textual.screen import ModalScreen
from textual.app import App, ComposeResult
from typing import Optional, ClassVar
from taskaway.taskaway_types import ColumnDefinitions
from textual.binding import Binding, BindingType


class ColumnLayoutScreen(ModalScreen):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "return", "Exit and save layout", show=True),
        Binding("m", "toggle_move", "Toggle move row", show=True),
        Binding("k", "cursor_up", "Cursor up", show=True),
        Binding("j", "cursor_down", "Cursor down", show=True),
    ]

    def __init__(self, column_definitions: ColumnDefinitions) -> None:
        self.column_definitions = column_definitions
        super().__init__()

    def compose(self) -> ComposeResult:
        yield SelectionList[int]()
        yield Label(r"\[j/k]:down/up \[enter]:select \[m]:toggle move \[esc]:save")

    def on_mount(self) -> None:
        self.move_mode = False
        self.redraw()
        self.get_selection_list().highlighted = 0

    def move_highlighted_column(self, offset: int):
        selection_list: SelectionList = self.get_selection_list()
        highlighted_index: Optional[int] = selection_list.highlighted

        if highlighted_index is None:
            return

        self.store_state()
        new_index: int = max(0, min(len(self.column_definitions) - 1, highlighted_index + offset))

        tmp = self.column_definitions[highlighted_index]
        self.column_definitions[highlighted_index] = self.column_definitions[new_index]
        self.column_definitions[new_index] = tmp

        self.redraw()

        selection_list: SelectionList = self.get_selection_list()
        selection_list.highlighted = new_index

    def get_selection_list(self) -> SelectionList:
        return self.query_one(SelectionList)

    def action_cursor_down(self) -> None:
        if self.move_mode:
            self.move_highlighted_column(1)
        else:
            self.get_selection_list().action_cursor_down()

    def action_cursor_up(self) -> None:
        if self.move_mode:
            self.move_highlighted_column(-1)
        else:
            self.get_selection_list().action_cursor_up()

    def action_toggle_move(self) -> None:
        self.move_mode = not self.move_mode

    def action_return(self):
        self.store_state()
        self.dismiss(self.column_definitions)

    def store_state(self) -> None:
        selection_list: SelectionList = self.get_selection_list()
        selected: list[int] = selection_list.selected
        for i in range(len(self.column_definitions)):
            column, _ = self.column_definitions[i]
            self.column_definitions[i] = (column, i in selected)

    def redraw(self) -> None:
        selection_list = self.query_one(SelectionList)
        selection_list.clear_options()

        for i in range(len(self.column_definitions)):
            column, selected = self.column_definitions[i]
            selection_list.add_option((column, i, selected))


class MainWindow(App):
    @work
    async def on_mount(self) -> None:
        await self.push_screen_wait(
            ColumnLayoutScreen(
                column_definitions=[
                    ("test1", True),
                    ("test2", False),
                    ("test3", True),
                    ("test4", False),
                ]
            )
        )


def start_application() -> None:
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    start_application()
