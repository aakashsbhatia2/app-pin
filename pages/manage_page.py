from __future__ import annotations

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib

from shortcut import InstalledShortcut, delete_shortcut, list_shortcuts


class ManagePage(Gtk.Box):
    """List page: shows app-pin shortcuts and lets the user delete them."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_border_width(16)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-activated", self._on_row_activated)
        scroller.add(self.listbox)
        self.pack_start(scroller, True, True, 0)

        self.status = Gtk.Label(xalign=0)
        self.pack_start(self.status, False, False, 0)

        button_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", lambda _: self.refresh())
        delete_btn = Gtk.Button(label="Delete selected")
        delete_btn.get_style_context().add_class("destructive-action")
        delete_btn.connect("clicked", self._on_delete)
        button_row.pack_start(refresh_btn, False, False, 0)
        button_row.pack_end(delete_btn, False, False, 0)
        self.pack_start(button_row, False, False, 0)

        self._rows: dict[Gtk.ListBoxRow, InstalledShortcut] = {}
        self.refresh()

    def refresh(self):
        for child in list(self.listbox.get_children()):
            self.listbox.remove(child)
        self._rows.clear()

        shortcuts = list_shortcuts()
        for s in shortcuts:
            row = self._build_row(s)
            self.listbox.add(row)
            self._rows[row] = s
        self.listbox.show_all()

        if not shortcuts:
            self._show("No shortcuts created yet.")
        else:
            self._show(f"{len(shortcuts)} shortcut(s).")

    @staticmethod
    def _build_row(s: InstalledShortcut) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_border_width(8)

        img = Gtk.Image()
        img.set_size_request(40, 40)
        if s.icon_path is not None and s.icon_path.exists():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(s.icon_path), 40, 40, True)
                img.set_from_pixbuf(pixbuf)
            except GLib.Error:
                pass
        hbox.pack_start(img, False, False, 0)

        name_lbl = Gtk.Label(xalign=0)
        name_lbl.set_markup(f"<b>{GLib.markup_escape_text(s.name)}</b>")
        hbox.pack_start(name_lbl, True, True, 0)

        row.add(hbox)
        return row

    def _show(self, msg: str, error: bool = False):
        color = "#c0392b" if error else "#444444"
        self.status.set_markup(f'<span foreground="{color}">{GLib.markup_escape_text(msg)}</span>')

    def _on_row_activated(self, _listbox, _row):
        # Double-click / Enter triggers delete on the active row.
        self._on_delete(None)

    def _on_delete(self, _btn):
        row = self.listbox.get_selected_row()
        if row is None:
            self._show("Select a shortcut first.", error=True)
            return
        shortcut = self._rows.get(row)
        if shortcut is None:
            return

        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"Delete \"{shortcut.name}\"?",
        )
        dialog.format_secondary_text("The .desktop entry and copied icon will be removed.")
        resp = dialog.run()
        dialog.destroy()
        if resp != Gtk.ResponseType.OK:
            return

        try:
            delete_shortcut(shortcut)
        except OSError as e:
            self._show(f"Couldn't delete: {e}", error=True)
            return
        self.refresh()
        self._show(f"Deleted: {shortcut.name}")
