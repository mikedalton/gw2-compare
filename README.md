# gw2-compare

## Purpose

This is a console-based application for interacting with the [Guild Wars 2 API](https://wiki.guildwars2.com/wiki/API:Main) to track, and optionally, do comparison math on groups of items.

## Functionality

The app allows you to create one or more groups to which you can add items by their Guild Wars 2 API ID number as well as a quantity of said item. Upon load, the app uses the [Items endpoint](https://wiki.guildwars2.com/wiki/API:2/items) to retrieve the item name and the [Trading Post Prices endpoint](https://wiki.guildwars2.com/wiki/API:2/commerce/prices) to retrieve the highest buy order price and the lowest sell order price. It then lists the item name, buy order and sell order prices, and both multiplied by the quantity.

All item groups allow the order of items in the list to be changed.

### Simple item groups

These groups have no relation between items.

### Promotion item groups

These groups use item hierarchy to calculate the gain or loss in converting the set quantity of an item into a single item of the item above it in the list.

## Data persistence

All groups, group settings, item IDs, and quantities are saved in [config.yaml](config.yaml). 