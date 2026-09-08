"""Config: loads credentials from .env in the repo root into os.environ.

Copy .env.example to .env and fill in your keys. Values already present in the
environment (e.g. set by systemd, docker, or your shell) always win — .env only
fills the gaps.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Where the app WRITES (API keys, tracked claims, check log). Defaults to the repo
# root; a PaaS / systemd unit with a read-only release sets DATA_DIR to a
# persistent writable directory instead (caddy-gui injects /var/lib/paas-<id>).
DATA_DIR = Path(os.environ.get("DATA_DIR") or ROOT)
_LOADED = False


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load() -> None:
    global _LOADED
    if _LOADED:
        return
    _load_env_file(ROOT / ".env")
    _LOADED = True


def get(key: str, default=None):
    load()
    return os.environ.get(key, default)


def require(key: str) -> str:
    v = get(key)
    if not v:
        raise RuntimeError(f"Missing required credential: {key} (set it in .env — see .env.example)")
    return v
