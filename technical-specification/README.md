# Technical specification

Implementation details for [app-pin](../README.md).

## The UI

| Field          | Purpose                                                              |
| -------------- | -------------------------------------------------------------------- |
| Name           | The display name shown in the menu. Auto-filled from the executable. |
| Executable     | Any binary, script, or AppImage. Made `+x` automatically if needed.  |
| Icon image     | PNG / JPG / SVG / etc. A 64px preview is shown next to the picker.   |
| Comment        | Optional tooltip text shown in the menu.                             |

The window is a `Gtk.Stack` driven by a `Gtk.StackSwitcher` with two children:

- **Create** — the form above.
- **Manage** — a `Gtk.ListBox` listing every shortcut app-pin has created.
  Re-scans disk on tab switch and after every delete.

## What gets written, and where

When you click **Create shortcut**, two files are created:

1. **Icon copy** at
   `~/.local/share/icons/app-pin/<slug><ext>`
   The icon is copied (not referenced in place) so the shortcut keeps working
   if you later move or delete the source image.

2. **Desktop entry** at
   `~/.local/share/applications/app-pin-<slug>.desktop`
   with contents like:

   ```
   [Desktop Entry]
   Type=Application
   Version=1.0
   Name=My Cool App
   Exec='/home/you/bin/my-cool-app'
   Icon=/home/you/.local/share/icons/app-pin/my-cool-app.png
   Terminal=false
   Categories=Utility;
   StartupNotify=true
   ```

`<slug>` is the name lowercased with non-alphanumerics replaced by `-`.

After writing, the app runs `update-desktop-database` so the new entry is
indexed immediately — no logout required.

## Installing app-pin itself as a real app

App Pin's whole job is to make `.desktop` shortcuts, so the easiest way to give
it a menu entry is to run it once and point it at its own script:

1. `python3 app_pin.py`
2. In the **Create** tab:
   - **Name:** `App Pin`
   - **Executable:** the absolute path to `app_pin.py` in this project. It
     already has `#!/usr/bin/env python3` and `+x`, so it runs directly.
   - **Icon image:** any PNG / SVG you like.
3. Click **Create shortcut**. It appears in GNOME activities immediately.

**Why this works:** when you run `python3 /path/to/app_pin.py`, Python
automatically adds that file's directory to `sys.path`, so `from pages import …`
and `from shortcut import …` resolve no matter what CWD the desktop
environment launched you from.

**Caveat:** the generated `.desktop` file hard-codes the absolute path to
`app_pin.py`. If you move the project folder, delete the shortcut from the
Manage tab and create a new one.

## Code map

```
app-pin/
├── app_pin.py          # entry point — window + Gtk.Stack hosting both pages
├── shortcut.py         # model + disk I/O — no GTK
└── pages/
    ├── __init__.py
    ├── create_page.py  # CreatePage: form for making a new shortcut
    └── manage_page.py  # ManagePage: list + delete existing shortcuts
```

- **`shortcut.py`** — pure logic, no GTK.
  - `ShortcutSpec` (dataclass) + `ShortcutSpec.validate()` (returns errors).
  - `write_shortcut(spec)` — chmods exec, copies icon, writes `.desktop`,
    refreshes the desktop database.
  - `InstalledShortcut` (dataclass) + `list_shortcuts()` — scans
    `~/.local/share/applications/app-pin-*.desktop` and parses each one.
  - `delete_shortcut(shortcut)` — removes the `.desktop` entry and any icon
    we copied into `~/.local/share/icons/app-pin/`. Other icons are left
    alone in case they're shared.
- **`pages/create_page.py`** — `CreatePage(Gtk.Box)` builds the form, owns the
  signal handlers, and on create: builds a `ShortcutSpec` from the form,
  calls `validate()`, calls `write_shortcut()`, reports the outcome.
- **`pages/manage_page.py`** — `ManagePage(Gtk.Box)` renders each
  `InstalledShortcut` as a row (icon + name), with a "Delete selected" button
  that confirms then calls `delete_shortcut()`. Re-scans disk whenever the
  user switches to the Manage tab.
- **`app_pin.py`** — thin entry point: creates the window, puts both pages in
  a `Gtk.Stack` driven by a `Gtk.StackSwitcher`, and refreshes the Manage page
  whenever it's brought to the front.

## Removing a shortcut manually

The Manage tab is the easy way. If you ever need to do it by hand:

```
rm ~/.local/share/applications/app-pin-<slug>.desktop
rm ~/.local/share/icons/app-pin/<slug>.*
update-desktop-database ~/.local/share/applications
```
