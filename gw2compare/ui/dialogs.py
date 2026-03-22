"""Modal dialogs for adding groups and items."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, RadioButton, RadioSet


class AddGroupModal(ModalScreen[tuple[str, str] | None]):
    """Modal to create a new group. Returns (name, type) or None on cancel."""

    DEFAULT_CSS = """
    AddGroupModal {
        align: center middle;
    }
    AddGroupModal > Vertical {
        width: 50;
        height: auto;
        border: thick $primary;
        padding: 1 2;
        background: $surface;
    }
    AddGroupModal Label {
        margin-bottom: 1;
    }
    AddGroupModal Input {
        margin-bottom: 1;
    }
    AddGroupModal RadioSet {
        margin-bottom: 1;
    }
    AddGroupModal Horizontal {
        height: auto;
        align-horizontal: right;
    }
    AddGroupModal Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("New Group", id="dialog-title")
            yield Label("Name:")
            yield Input(placeholder="Group name", id="name-input")
            yield Label("Type:")
            with RadioSet(id="type-radio"):
                yield RadioButton("Simple", value=True, id="radio-simple")
                yield RadioButton("Promotion", id="radio-promotion")
            with Horizontal():
                yield Button("Cancel", variant="default", id="cancel-btn")
                yield Button("Add", variant="primary", id="confirm-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "confirm-btn":
            name = self.query_one("#name-input", Input).value.strip()
            if not name:
                return
            radio_set = self.query_one("#type-radio", RadioSet)
            group_type = "promotion" if radio_set.pressed_index == 1 else "simple"
            self.dismiss((name, group_type))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.query_one("#confirm-btn", Button).press()


class AddItemModal(ModalScreen[tuple[int, int] | None]):
    """Modal to add an item to a group. Returns (item_id, quantity) or None on cancel."""

    DEFAULT_CSS = """
    AddItemModal {
        align: center middle;
    }
    AddItemModal > Vertical {
        width: 50;
        height: auto;
        border: thick $primary;
        padding: 1 2;
        background: $surface;
    }
    AddItemModal Label {
        margin-bottom: 1;
    }
    AddItemModal Input {
        margin-bottom: 1;
    }
    AddItemModal Horizontal {
        height: auto;
        align-horizontal: right;
    }
    AddItemModal Button {
        margin-left: 1;
    }
    AddItemModal #error-label {
        color: $error;
        height: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Add Item", id="dialog-title")
            yield Label("Item ID:")
            yield Input(placeholder="e.g. 24295", id="id-input")
            yield Label("Quantity:")
            yield Input(placeholder="e.g. 100", value="1", id="qty-input")
            yield Label("", id="error-label")
            with Horizontal():
                yield Button("Cancel", variant="default", id="cancel-btn")
                yield Button("Add", variant="primary", id="confirm-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "confirm-btn":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        error_label = self.query_one("#error-label", Label)
        id_str = self.query_one("#id-input", Input).value.strip()
        qty_str = self.query_one("#qty-input", Input).value.strip()

        try:
            item_id = int(id_str)
            if item_id <= 0:
                raise ValueError
        except ValueError:
            error_label.update("Item ID must be a positive integer.")
            return

        try:
            quantity = int(qty_str)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            error_label.update("Quantity must be a positive integer.")
            return

        self.dismiss((item_id, quantity))


class EditQuantityModal(ModalScreen[int | None]):
    """Modal to edit the quantity of an existing item. Returns new quantity or None."""

    DEFAULT_CSS = """
    EditQuantityModal {
        align: center middle;
    }
    EditQuantityModal > Vertical {
        width: 40;
        height: auto;
        border: thick $primary;
        padding: 1 2;
        background: $surface;
    }
    EditQuantityModal Label {
        margin-bottom: 1;
    }
    EditQuantityModal Input {
        margin-bottom: 1;
    }
    EditQuantityModal Horizontal {
        height: auto;
        align-horizontal: right;
    }
    EditQuantityModal Button {
        margin-left: 1;
    }
    EditQuantityModal #error-label {
        color: $error;
        height: 1;
    }
    """

    def __init__(self, current_qty: int) -> None:
        super().__init__()
        self._current_qty = current_qty

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Edit Quantity")
            yield Input(value=str(self._current_qty), id="qty-input")
            yield Label("", id="error-label")
            with Horizontal():
                yield Button("Cancel", variant="default", id="cancel-btn")
                yield Button("Save", variant="primary", id="confirm-btn")

    def on_mount(self) -> None:
        inp = self.query_one("#qty-input", Input)
        inp.focus()
        inp.cursor_position = len(inp.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "confirm-btn":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        error_label = self.query_one("#error-label", Label)
        qty_str = self.query_one("#qty-input", Input).value.strip()
        try:
            quantity = int(qty_str)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            error_label.update("Quantity must be a positive integer.")
            return
        self.dismiss(quantity)
