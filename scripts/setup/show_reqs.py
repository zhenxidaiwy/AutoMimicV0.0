"""Print declared requirements of the mjlab stack (to find mutually compatible pins)."""
from importlib.metadata import requires, version

if __name__ == "__main__":
    for pkg in ["mjlab", "mujoco-warp", "warp-lang", "mujoco", "rsl-rl-lib", "torch"]:
        try:
            reqs = [r for r in (requires(pkg) or []) if "extra ==" not in r]
            print(f"{pkg}=={version(pkg)}: {reqs}")
        except Exception as e:
            print(pkg, "?", e)
