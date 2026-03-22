"""MainScreen: tiled grid layout of group panels."""

from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Label

from ..api import GW2Client
from ..config import AppConfig, Group, GroupType, save_config
from .group_panel import GroupPanel


class MainScreen(Vertical):
    """Scrollable grid of GroupPanel tiles."""

    DEFAULT_CSS = """
    MainScreen {
        height: 1fr;
    }
    MainScreen > VerticalScroll {
        height: 1fr;
    }
    #tiles-grid {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 1fr;
        padding: 1;
    }
    GroupPanel {
        height: 30;
        margin: 1;
        border: tall $surface-darken-2;
    }
    GroupPanel.active {
        border: tall $primary;
    }
    """

    BINDINGS = [
        Binding("g", "add_group", "Add Group"),
        Binding("G", "add_group", "Add Group", show=False),
        Binding("a", "add_item", "Add Item"),
        Binding("A", "add_item", "Add Item", show=False),
        Binding("e", "edit_quantity", "Edit Qty"),
        Binding("E", "edit_quantity", "Edit Qty", show=False),
        Binding("d", "delete_item", "Delete Item"),
        Binding("D", "delete_item", "Delete Item", show=False),
        Binding("u", "move_up", "Move Up"),
        Binding("U", "move_up", "Move Up", show=False),
        Binding("j", "move_down", "Move Down"),
        Binding("J", "move_down", "Move Down", show=False),
        Binding("r", "refresh", "Refresh"),
        Binding("R", "refresh", "Refresh", show=False),
        Binding("ctrl+r", "refresh_all", "Refresh All"),
    ]

    def __init__(self, cfg: AppConfig, client: GW2Client) -> None:
        super().__init__()
        self._cfg = cfg
        self._client = client
        self._active_panel: GroupPanel | None = None

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Container(id="tiles-grid")

    def on_mount(self) -> None:
        grid = self.query_one("#tiles-grid", Container)
        for group in self._cfg.groups:
            grid.mount(GroupPanel(group=group, cfg=self._cfg, client=self._client))
        panels = list(self.query(GroupPanel))
        if panels:
            self._set_active(panels[0])

    def on_group_panel_activated(self, event: GroupPanel.Activated) -> None:
        self._set_active(event.panel)

    def _set_active(self, panel: GroupPanel) -> None:
        if self._active_panel:
            self._active_panel.is_active = False
        self._active_panel = panel
        panel.is_active = True
        panel.focus_table()

    def action_add_group(self) -> None:
        from .dialogs import AddGroupModal

        def handle_result(result: tuple[str, str] | None) -> None:
            if result is None:
                return
            name, gtype = result
            new_group = Group(name=name, type=GroupType(gtype))
            self._cfg.groups.append(new_group)
            save_config(self._cfg)
            panel = GroupPanel(group=new_group, cfg=self._cfg, client=self._client)
            grid = self.query_one("#tiles-grid", Container)
            grid.mount(panel)
            self._set_active(panel)

        self.app.push_screen(AddGroupModal(), handle_result)

    def action_add_item(self) -> None:
        if self._active_panel:
            self._active_panel.action_add_item()

    def action_edit_quantity(self) -> None:
        if self._active_panel:
            self._active_panel.action_edit_quantity()

    def action_delete_item(self) -> None:
        if self._active_panel:
            self._active_panel.action_delete_item()

    def action_move_up(self) -> None:
        if self._active_panel:
            self._active_panel.action_move_up()

    def action_move_down(self) -> None:
        if self._active_panel:
            self._active_panel.action_move_down()

    def action_refresh(self) -> None:
        if self._active_panel:
            self._client.clear_cache()
            self.run_worker(self._active_panel.refresh_data(), name="refresh")
            self.app.notify(f"Refreshed at {datetime.now().strftime('%H:%M:%S')}")

    def action_refresh_all(self) -> None:
        self._client.clear_cache()
        for panel in self.query(GroupPanel):
            self.run_worker(panel.refresh_data(), name=f"refresh-{id(panel)}")
        self.app.notify(f"All refreshed at {datetime.now().strftime('%H:%M:%S')}")
