"""GroupPanel widget: renders one group's item table and promotion summary."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable, Label, LoadingIndicator, Static

from ..api import GW2Client, ItemData, format_price
from ..config import AppConfig, Group, GroupType, Item, save_config
from ..math import calc_promotion, PromotionStep


SIMPLE_COLUMNS = ("Item Name", "Qty", "Buy", "Sell", "Qty×Buy", "Qty×Sell")
PROMOTION_COLUMNS = ("Item Name", "Req Qty", "Req×Buy", "Req×Sell")


class PromotionSummary(Static):
    """Renders promotion step math below the DataTable."""

    DEFAULT_CSS = """
    PromotionSummary {
        height: auto;
        padding: 1 0;
        border-top: solid $primary-darken-2;
    }
    """

    def __init__(self, steps: list[PromotionStep]) -> None:
        super().__init__()
        self._steps = steps

    def render(self) -> str:
        if not self._steps:
            return "[dim]No promotion data available.[/dim]"
        lines: list[str] = ["[bold]Promotion Steps[/bold]"]
        for idx, step in enumerate(self._steps, 1):
            lower_str = format_price(step.lower_value)
            upper_str = format_price(step.upper_value)
            sign = "+" if step.delta >= 0 else ""
            colour = "green" if step.delta >= 0 else "red"
            delta_str = f"[{colour}]{sign}{format_price(abs(step.delta))}[/{colour}]"
            lines.append(
                f"  Step {idx}: {step.quantity}× {step.lower_item.name} → 1× {step.upper_item.name}"
            )
            lines.append(f"    {lower_str} → {upper_str}  ({delta_str})")
        return "\n".join(lines)


class GroupPanel(Vertical):
    """Tile widget that displays the items in a single group."""

    class Activated(Message):
        """Posted when this tile is clicked."""
        def __init__(self, panel: "GroupPanel") -> None:
            super().__init__()
            self.panel = panel

    is_active: reactive[bool] = reactive(False)

    def watch_is_active(self, active: bool) -> None:
        self.set_class(active, "active")

    def on_click(self) -> None:
        self.post_message(self.Activated(self))

    DEFAULT_CSS = """
    GroupPanel {
        padding: 0 1;
        overflow-y: auto;
    }
    GroupPanel #panel-title {
        height: 3;
        content-align: left middle;
        padding: 0 1;
        color: $text;
        text-style: bold;
        border-bottom: solid $primary-darken-2;
    }
    GroupPanel #keybind-hint {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    GroupPanel #loading {
        height: 3;
    }
    GroupPanel DataTable {
        height: auto;
    }
    """

    def __init__(self, group: Group, cfg: AppConfig, client: GW2Client) -> None:
        super().__init__()
        self._group = group
        self._cfg = cfg
        self._client = client
        self._item_data: dict[int, ItemData] = {}

    def compose(self) -> ComposeResult:
        type_label = "Simple" if self._group.type == GroupType.SIMPLE else "Promotion"
        yield Label(f"{self._group.name}  [{type_label}]", id="panel-title")
        yield Label(
            "[a] Add item  [e] Edit qty  [d] Delete  [u/j] Move up/down",
            id="keybind-hint",
        )
        yield LoadingIndicator(id="loading")
        yield DataTable(id="item-table", show_cursor=True)

    def on_mount(self) -> None:
        table = self.query_one("#item-table", DataTable)
        cols = PROMOTION_COLUMNS if self._group.type == GroupType.PROMOTION else SIMPLE_COLUMNS
        table.add_columns(*cols)
        table.cursor_type = "row"
        self.run_worker(self._fetch_and_render(), exclusive=True, name="fetch")

    def focus_table(self) -> None:
        try:
            self.query_one("#item-table", DataTable).focus()
        except Exception:
            pass

    async def _fetch_and_render(self) -> None:
        item_ids = [i.item_id for i in self._group.items]
        if item_ids:
            self._item_data = await self._client.fetch_many(item_ids)
        self._render_table()
        try:
            self.query_one("#loading", LoadingIndicator).remove()
        except Exception:
            pass
        if self._group.type == GroupType.PROMOTION:
            self._render_promotion()
        if self.is_active:
            self.focus_table()

    def _render_table(self) -> None:
        table = self.query_one("#item-table", DataTable)
        table.clear()
        if self._group.type == GroupType.PROMOTION:
            self._render_promotion_rows(table)
        else:
            self._render_simple_rows(table)

    def _render_simple_rows(self, table: DataTable) -> None:
        for item in self._group.items:
            data = self._item_data.get(item.item_id)
            name = data.name if data else f"Unknown ({item.item_id})"
            buy = format_price(data.buy_price) if data else "-"
            sell = format_price(data.sell_price) if data else "-"
            qty_buy = format_price(data.buy_price * item.quantity) if data else "-"
            qty_sell = format_price(data.sell_price * item.quantity) if data else "-"
            table.add_row(name, str(item.quantity), buy, sell, qty_buy, qty_sell)

    def _render_promotion_rows(self, table: DataTable) -> None:
        # Calculate cumulative required quantity for each item to produce 1 of the top tier.
        # items[0] is the top tier (req=1); for items[i>0], req = product of items[1..i].quantity.
        req_qtys: list[int] = []
        cumulative = 1
        for i, item in enumerate(self._group.items):
            if i == 0:
                req_qtys.append(1)
            else:
                cumulative *= item.quantity
                req_qtys.append(cumulative)

        for item, req_qty in zip(self._group.items, req_qtys):
            data = self._item_data.get(item.item_id)
            name = data.name if data else f"Unknown ({item.item_id})"
            req_buy = format_price(data.buy_price * req_qty) if data else "-"
            req_sell = format_price(data.sell_price * req_qty) if data else "-"
            table.add_row(name, str(req_qty), req_buy, req_sell)

    def _render_promotion(self) -> None:
        # Remove old summary if present
        for widget in self.query("PromotionSummary"):
            widget.remove()
        steps = calc_promotion(self._group.items, self._item_data)
        self.mount(PromotionSummary(steps))

    async def refresh_data(self) -> None:
        """Re-fetch prices (cache already cleared by caller) and re-render."""
        try:
            loading = LoadingIndicator(id="loading")
            await self.mount(loading, before=self.query_one("#item-table"))
        except Exception:
            pass
        self.run_worker(self._fetch_and_render(), exclusive=True, name="fetch")

    def _current_row_index(self) -> int | None:
        table = self.query_one("#item-table", DataTable)
        if table.row_count == 0:
            return None
        return table.cursor_row

    def action_add_item(self) -> None:
        """Triggered by parent app via keybinding."""
        from .dialogs import AddItemModal

        def handle_result(result: tuple[int, int] | None) -> None:
            if result is None:
                return
            item_id, quantity = result
            self._group.items.append(Item(item_id=item_id, quantity=quantity))
            save_config(self._cfg)
            self.run_worker(self._fetch_and_render(), exclusive=True, name="fetch")

        self.app.push_screen(AddItemModal(), handle_result)

    def action_delete_item(self) -> None:
        idx = self._current_row_index()
        if idx is None:
            return
        del self._group.items[idx]
        save_config(self._cfg)
        self._render_table()
        if self._group.type == GroupType.PROMOTION:
            self._render_promotion()

    def action_move_up(self) -> None:
        idx = self._current_row_index()
        if idx is None or idx == 0:
            return
        items = self._group.items
        items[idx - 1], items[idx] = items[idx], items[idx - 1]
        save_config(self._cfg)
        self._render_table()
        table = self.query_one("#item-table", DataTable)
        table.move_cursor(row=idx - 1)
        if self._group.type == GroupType.PROMOTION:
            self._render_promotion()

    def action_move_down(self) -> None:
        idx = self._current_row_index()
        if idx is None or idx >= len(self._group.items) - 1:
            return
        items = self._group.items
        items[idx + 1], items[idx] = items[idx], items[idx + 1]
        save_config(self._cfg)
        self._render_table()
        table = self.query_one("#item-table", DataTable)
        table.move_cursor(row=idx + 1)
        if self._group.type == GroupType.PROMOTION:
            self._render_promotion()

    def action_edit_quantity(self) -> None:
        idx = self._current_row_index()
        if idx is None:
            return
        current_qty = self._group.items[idx].quantity

        from .dialogs import EditQuantityModal

        def handle_result(result: int | None) -> None:
            if result is None:
                return
            self._group.items[idx].quantity = result
            save_config(self._cfg)
            self._render_table()
            if self._group.type == GroupType.PROMOTION:
                self._render_promotion()
            table = self.query_one("#item-table", DataTable)
            table.move_cursor(row=idx)
            self.focus_table()

        self.app.push_screen(EditQuantityModal(current_qty), handle_result)
