# app-pin

A small Ubuntu GUI that turns any executable + image into a proper desktop
shortcut — searchable from GNOME activities, pinnable to the dock, indistinguishable
from any other installed app.

## How to use it

- Launch the app: `python3 app_pin.py`
- **Create** tab — make a new shortcut:
  - Pick an executable (binary, script, or AppImage)
  - Pick an icon image (PNG / JPG / SVG / etc.)
  - Give it a name (auto-filled from the filename)
  - Optionally add a comment for the tooltip
  - Click **Create shortcut** — it appears in the activities search immediately
- **Manage** tab — review every shortcut you've made:
  - Select one and click **Delete selected** (or double-click a row) to remove it
  - Hit **Refresh** to re-scan disk on demand

Only dependency is PyGObject + GTK 3, which ship with Ubuntu by default.

**Bonus:** `app_pin.py` itself can be turned into a menu entry — just run app-pin
and point it at its own script. See the technical spec for the exact steps.

## More

See [`technical-specification/README.md`](technical-specification/README.md)
for the file layout, what gets written where, the code map, and how to install
app-pin itself as a real menu entry.
