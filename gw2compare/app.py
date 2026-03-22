"""Textual App entry point for gw2-compare."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from .api import GW2Client
from .config import load_config, AppConfig
from .ui.main_screen import MainScreen


class GW2App(App):
    TITLE = "gw2-compare"
    SUB_TITLE = "Guild Wars 2 Trading Post Tracker"

    CSS = """
    Screen {
        layout: vertical;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("Q", "quit", "Quit", priority=True, show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._cfg: AppConfig = load_config()
        self._client: GW2Client = GW2Client()

    def compose(self) -> ComposeResult:
        yield Header()
        yield MainScreen(cfg=self._cfg, client=self._client)
        yield Footer()

    async def on_unmount(self) -> None:
        await self._client.close()


def run() -> None:
    GW2App().run()
