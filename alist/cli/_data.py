from platformdirs import PlatformDirs
from rich.console import Console
import os

_dirs = PlatformDirs("alist3")


class dirs:
    auths = os.path.join(_dirs.user_data_dir, "users")

    @staticmethod
    def init():
        for k, v in dirs.__dict__.items():
            if k.startswith("_"):
                continue
            if k == "init":
                continue
            if not os.path.exists(v):
                os.makedirs(v)


dirs.init()
console = Console()
