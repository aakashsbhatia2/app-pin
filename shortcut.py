"""Pure model + disk I/O for creating freedesktop .desktop shortcuts.

No GTK imports — safe to call from tests, a CLI, or any other UI.
"""
from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

APPS_DIR = Path.home() / ".local" / "share" / "applications"
ICONS_DIR = Path.home() / ".local" / "share" / "icons" / "app-pin"

ICON_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".xpm", ".gif", ".webp", ".bmp", ".ico"}


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", name.strip()).strip("-").lower()
    return slug or "shortcut"


@dataclass
class ShortcutSpec:
    name: str
    executable: Path | None
    icon: Path | None
    comment: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.name.strip():
            errors.append("Please enter a name.")
        if self.executable is None or not self.executable.exists():
            errors.append("Please pick a valid executable.")
        if self.icon is None or not self.icon.exists():
            errors.append("Please pick a valid icon image.")
        return errors


def write_shortcut(spec: ShortcutSpec) -> Path:
    """Materialise a validated ShortcutSpec on disk. Returns the .desktop path."""
    assert spec.executable is not None and spec.icon is not None, "call validate() first"

    exec_p = spec.executable
    if not os.access(exec_p, os.X_OK):
        exec_p.chmod(exec_p.stat().st_mode | 0o111)

    APPS_DIR.mkdir(parents=True, exist_ok=True)
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    slug = slugify(spec.name)
    icon_dest = ICONS_DIR / f"{slug}{spec.icon.suffix.lower()}"
    shutil.copyfile(spec.icon, icon_dest)

    contents = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Version=1.0\n"
        f"Name={spec.name}\n"
        f"Exec={shlex.quote(str(exec_p))}\n"
        f"Icon={icon_dest}\n"
        "Terminal=false\n"
        "Categories=Utility;\n"
        "StartupNotify=true\n"
    )
    if spec.comment:
        contents += f"Comment={spec.comment}\n"

    desktop_file = APPS_DIR / f"app-pin-{slug}.desktop"
    desktop_file.write_text(contents)
    desktop_file.chmod(0o755)

    _refresh_desktop_db()
    return desktop_file


@dataclass
class InstalledShortcut:
    desktop_path: Path
    name: str
    icon_path: Path | None


def list_shortcuts() -> list[InstalledShortcut]:
    """Return every shortcut app-pin has created, parsed from disk."""
    if not APPS_DIR.exists():
        return []
    return sorted(
        (_parse_shortcut(p) for p in APPS_DIR.glob("app-pin-*.desktop")),
        key=lambda s: s.name.lower(),
    )


def _parse_shortcut(path: Path) -> InstalledShortcut:
    name = path.stem
    icon: Path | None = None
    try:
        for line in path.read_text().splitlines():
            if line.startswith("Name="):
                name = line[len("Name="):]
            elif line.startswith("Icon="):
                icon = Path(line[len("Icon="):])
    except OSError:
        pass
    return InstalledShortcut(desktop_path=path, name=name, icon_path=icon)


def delete_shortcut(shortcut: InstalledShortcut) -> None:
    """Remove a shortcut's .desktop entry and any icon we copied for it."""
    shortcut.desktop_path.unlink(missing_ok=True)
    icon = shortcut.icon_path
    if icon is not None and icon.is_relative_to(ICONS_DIR):
        icon.unlink(missing_ok=True)
    _refresh_desktop_db()


def _refresh_desktop_db() -> None:
    subprocess.run(
        ["update-desktop-database", str(APPS_DIR)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
