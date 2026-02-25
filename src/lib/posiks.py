"""A collection of POSIX-like functions for file and system operations."""

import os
import time

import microcontroller


def _rjust(s: str, width: int) -> str:
    """Right-justify a string with spaces."""
    padding = width - len(s)
    return ' ' * padding + s if padding > 0 else s


def _format_size(size: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            if unit == 'B':
                return _rjust(str(size), 5)
            return _rjust(f"{size:.1f}{unit}", 5)
        size //= 1024
    return _rjust(f"{size:.1f}TB", 5)


def _is_dir(path: str) -> bool:
    """Check if a path is a directory."""
    dir_bit = 0b0100_0000_0000_0000
    return os.stat(path)[0] & dir_bit != 0


def cat(path: str):
    """Read and return the contents of a file."""
    with open(path, "r") as f:
        content = f.read()
    print(content)
    return content


def rm(path: str):
    """Remove a file."""
    if _is_dir(path):
        print(f"Error: '{path}' is a directory. Use rmdir to remove directories.")
        return
    os.remove(path)


def rmdir(path: str):
    """Remove a directory."""
    if not _is_dir(path):
        print(f"Error: '{path}' is not a directory. Use rm to remove files.")
        return
    os.rmdir(path)


def ls(path: str = '.'):
    """List files in a directory with details (like ls -la)."""
    lst = os.listdir(path)

    entries = []

    for item in lst:
        item_path = path + os.sep + item
        stat_info = os.stat(item_path)
        is_dir = _is_dir(item_path)

        size = stat_info[6]
        mtime = time.localtime(stat_info[8])
        mtime_str = f"{mtime[0]}-{mtime[1]:02d}-{mtime[2]:02d} {mtime[3]:02d}:{mtime[4]:02d}"
        size_str = _format_size(size)

        name = item + (os.sep if is_dir else "")
        entries.append((name, is_dir, size_str, mtime_str))

    # Sort directories first, then files
    entries.sort(key=lambda x: (not x[1], x[0]))

    for name, is_dir, size_str, mtime_str in entries:
        print(f"{size_str} {mtime_str} {name}")

    return lst


def touch(path: str):
    """Create an empty file or update its timestamp."""
    with open(path, "a"):
        pass


def reboot():
    """Reboot the system."""
    microcontroller.reset()


def uname():
    """Return system information."""
    uname_val = os.uname()
    print(' '.join(uname_val))
    return uname_val


def pwd():
    """Return the current working directory."""
    cwd = os.getcwd()
    print(cwd)
    return cwd

def env():
    return cat('/settings.toml')
