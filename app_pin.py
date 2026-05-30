#!/usr/bin/env python3
"""Entry point: a window with a Create page and a Manage page."""
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from pages import CreatePage, ManagePage


def main() -> int:
    win = Gtk.Window(title="App Pin")
    win.set_default_size(560, 440)
    win.connect("destroy", Gtk.main_quit)

    stack = Gtk.Stack()
    stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)

    create_page = CreatePage()
    manage_page = ManagePage()
    stack.add_titled(create_page, "create", "Create")
    stack.add_titled(manage_page, "manage", "Manage")

    # Re-scan disk whenever the user switches to the Manage tab.
    def on_switch(stack_, _pspec):
        if stack_.get_visible_child_name() == "manage":
            manage_page.refresh()
    stack.connect("notify::visible-child", on_switch)

    switcher = Gtk.StackSwitcher()
    switcher.set_stack(stack)
    switcher.set_halign(Gtk.Align.CENTER)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    outer.set_border_width(8)
    outer.pack_start(switcher, False, False, 0)
    outer.pack_start(stack, True, True, 0)
    win.add(outer)

    win.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
