from __future__ import annotations

from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib

from shortcut import ICON_EXTS, ShortcutSpec, write_shortcut


class CreatePage(Gtk.Box):
    """Form page: collects shortcut fields and hands them to the writer."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_border_width(16)

        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        self.pack_start(grid, True, True, 0)

        # Name
        grid.attach(self._label("Name"), 0, 0, 1, 1)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_placeholder_text("e.g. My Cool App")
        self.name_entry.set_hexpand(True)
        grid.attach(self.name_entry, 1, 0, 2, 1)

        # Executable
        grid.attach(self._label("Executable"), 0, 1, 1, 1)
        self.exec_btn = Gtk.FileChooserButton(title="Select executable")
        self.exec_btn.set_action(Gtk.FileChooserAction.OPEN)
        self.exec_btn.set_hexpand(True)
        self.exec_btn.connect("file-set", self._on_exec_chosen)
        grid.attach(self.exec_btn, 1, 1, 2, 1)

        # Icon
        grid.attach(self._label("Icon image"), 0, 2, 1, 1)
        self.icon_btn = Gtk.FileChooserButton(title="Select icon image")
        self.icon_btn.set_action(Gtk.FileChooserAction.OPEN)
        self.icon_btn.set_hexpand(True)
        icon_filter = Gtk.FileFilter()
        icon_filter.set_name("Image files")
        for ext in ICON_EXTS:
            icon_filter.add_pattern(f"*{ext}")
        self.icon_btn.add_filter(icon_filter)
        self.icon_btn.connect("file-set", self._on_icon_chosen)
        grid.attach(self.icon_btn, 1, 2, 1, 1)

        self.icon_preview = Gtk.Image()
        self.icon_preview.set_size_request(64, 64)
        grid.attach(self.icon_preview, 2, 2, 1, 1)

        # Comment
        grid.attach(self._label("Comment"), 0, 3, 1, 1)
        self.comment_entry = Gtk.Entry()
        self.comment_entry.set_placeholder_text("(optional) tooltip shown in the menu")
        grid.attach(self.comment_entry, 1, 3, 2, 1)

        # Status + action
        self.status = Gtk.Label(xalign=0)
        self.status.set_line_wrap(True)
        grid.attach(self.status, 0, 4, 3, 1)

        create_btn = Gtk.Button(label="Create shortcut")
        create_btn.get_style_context().add_class("suggested-action")
        create_btn.connect("clicked", self._on_create)
        grid.attach(create_btn, 0, 5, 3, 1)

    @staticmethod
    def _label(text: str) -> Gtk.Label:
        return Gtk.Label(label=text, xalign=1)

    def _on_exec_chosen(self, btn):
        path = btn.get_filename()
        if path and not self.name_entry.get_text().strip():
            self.name_entry.set_text(Path(path).stem.replace("-", " ").replace("_", " ").title())

    def _on_icon_chosen(self, btn):
        path = btn.get_filename()
        if not path:
            return
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 64, 64, True)
            self.icon_preview.set_from_pixbuf(pixbuf)
        except GLib.Error:
            self.icon_preview.clear()

    def _show(self, msg: str, error: bool = False):
        color = "#c0392b" if error else "#27ae60"
        self.status.set_markup(f'<span foreground="{color}">{GLib.markup_escape_text(msg)}</span>')

    def _build_spec(self) -> ShortcutSpec:
        exec_path = self.exec_btn.get_filename()
        icon_path = self.icon_btn.get_filename()
        return ShortcutSpec(
            name=self.name_entry.get_text().strip(),
            executable=Path(exec_path) if exec_path else None,
            icon=Path(icon_path) if icon_path else None,
            comment=self.comment_entry.get_text().strip(),
        )

    def _on_create(self, _btn):
        spec = self._build_spec()
        errors = spec.validate()
        if errors:
            self._show(errors[0], error=True)
            return
        try:
            path = write_shortcut(spec)
        except OSError as e:
            self._show(f"Couldn't create shortcut: {e}", error=True)
            return
        self._show(f"Created: {path}")
