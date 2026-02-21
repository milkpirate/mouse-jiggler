import os
import microcontroller


def cat(path: str):
    """Read and return the contents of a file."""
    with open(path, "r") as f:
        content = f.read()
    print(content)
    return content

def rm(path: str):
    """Remove a file."""
    os.remove(path)

def ls(path: str = '.'):
    """List files in a directory."""
    l = os.listdir(path)

    dir_bit = 0b0100_0000_0000_0000
    ds = [
        d for d in l
        if os.stat(path + os.sep + d)[0]
           & dir_bit
    ]
    ds = [d + os.sep for d in ds]
    fs = [f for f in l if f not in ds]

    ds.sort()
    fs.sort()

    [print(d) for d in ds]
    [print(f) for f in fs]
    return l

def touch(path: str):
    """Create an empty file or update its timestamp."""
    with open(path, "a"):
        pass

def reboot():
    """Reboot the system."""
    microcontroller.reset()

def uname():
    uname = os.uname()
    print(' '.join(uname))
    return uname

def pwd():
    cwd = os.getcwd()
    print(cwd)
    return cwd
