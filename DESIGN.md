# Design Decisions

This file tracks the rationale behind key architectural and product decisions.
Update it when decisions change or new decisions are made.

---

## Data Model

**`Item` stores only user-supplied data (item_id, quantity); runtime data lives in `GW2Client._cache`.**
The config file stays clean and predictable. Prices are always fetched fresh on startup (or on refresh), so caching them to disk would only add stale-data risk.

**Quantity on the top-tier item in a Promotion group is kept but ignored.**
Removing it would require a special case in the data model and YAML schema. Uniform schema is simpler. The `calc_promotion` function only reads `items[i].quantity` for the lower tier of each pair.

---

## API Client (`api.py`)

**`httpx.AsyncClient` over `aiohttp`.**
`httpx` has a cleaner API, supports both sync and async (useful for ad-hoc testing), and is well-maintained. Single shared client instance reuses connections.

**In-memory cache only (no disk persistence for prices).**
Prices change frequently. A disk cache would require expiry logic. Session-level cache is sufficient — `r` refreshes the active tile, `ctrl+r` refreshes all tiles.

**`fetch_many` uses `asyncio.gather` for concurrent per-item requests.**
The GW2 API supports bulk item queries (`/v2/items?ids=1,2,3`) but the prices endpoint does not support bulk in the same way in all versions. Per-item concurrent fetches keep the two endpoints symmetric and straightforward.

**Zero prices displayed as `-`.**
A zero price means either no buy orders / no sell listings exist. Displaying `0g 00s 00c` would be misleading. `-` clearly indicates no market data.

---

## Promotion Math (`math.py`)

**Promotion steps show value delta only; acquisition cost is ignored.**
The assumption is that the user already owns all the items. Each step shows:
`lower_value = quantity * lower_item.buy_price` vs. `upper_value = upper_item.buy_price`, and the delta between them.
Buy order price is used for both sides — it represents the best price you could get by selling into existing buy orders at each tier.

**Table columns differ by group type.**
Simple groups show: Item Name | Qty | Buy | Sell | Qty×Buy | Qty×Sell.
Promotion groups show: Item Name | Req Qty | Req×Buy | Req×Sell, where "Req Qty" is the cumulative number of that item needed to produce **one** of the top-tier item — the product of all quantities from that item up through the chain. The top-tier item itself always shows Req Qty = 1. This lets you see at a glance the total input cost at each tier.

**One `PromotionStep` per adjacent pair.**
Items are ordered highest → lowest tier (index 0 = top tier). Each step represents converting N of tier[i+1] into 1 of tier[i]. The `quantity` field belongs to the **lower** item in each pair — it tells you how many of that item are consumed to produce one of the item above it. The top-tier item's quantity is unused. Multiple conversion paths (e.g. T6→T5, T5→T4) are each shown as a separate step.

---

## UI Architecture (`ui/`)

**`DataTable` over custom `ItemRow` widgets.**
Textual's `DataTable` provides column headers, keyboard navigation, and row cursor for free. Custom widgets would allow inline editing and drag-and-drop reordering but require significantly more code. Keybinding-based reorder (`u`/`j`) is sufficient.

**Single `MainScreen` (no multi-screen navigation).**
There is no navigation depth warranting multiple screens. Modals (`ModalScreen`) handle all data-entry flows.

**Tile grid layout, not sidebar + panel.**
All groups are displayed simultaneously as tiles in a 2-column CSS grid. `MainScreen` is a `VerticalScroll` containing a `Container` with `layout: grid`. This replaces the original sidebar-select model. The active tile is highlighted with a `$primary` border; inactive tiles use a dimmed border.

**All groups fetch on startup (no lazy fetch).**
Since all tiles are mounted at once, each `GroupPanel.on_mount` fires its own `run_worker(self._fetch_and_render())` concurrently. The original lazy-fetch-on-select model no longer applies.

**`GroupPanel` owns its fetch worker.**
Textual's Worker API integrates with the event loop, avoids blocking the UI, and cancels automatically when the widget is removed.

**Active tile tracking.**
`GroupPanel` posts an `Activated` message when clicked. `MainScreen` handles this to toggle `is_active` on panels, which adds/removes the `.active` CSS class. The `DataTable` inside the active tile is explicitly focused on activation and after fetch completes, so arrow keys work immediately without requiring a Tab press.

**`r` refreshes active tile only; `ctrl+r` refreshes all tiles.**
Refreshing a single tile is the common case. Full refresh is available but kept as a secondary chord to avoid accidental mass API calls.

**Editing quantity recalculates from cached prices; does not re-fetch.**
When quantity is edited, `_render_table` is called directly with the updated quantity and existing `_item_data`. The API is not re-hit because unit prices haven't changed — only the multiplied totals need updating. Use `r` after an edit if fresh prices are also wanted. Cursor position is restored to the edited row after re-render.

---

## Config Schema (`config.yaml`)

```yaml
groups:
  - name: string
    type: simple | promotion
    items:
      - item_id: int
        quantity: int
```

No `version` key for now. Add `version: 1` when a breaking schema change requires migration logic.

---

## Price Formatting

All prices are stored as `int` (copper coins).

```
gold, remainder = divmod(copper, 10000)
silver, copper_r = divmod(remainder, 100)
```

Display: `Xg XXs XXc`. If gold is 0, omit it. If silver is 0, omit it. Always show copper.
Zero → `-` (no market data).
