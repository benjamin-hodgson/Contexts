import sys
from .plugin_discovery import load_plugins
from . import run_with_plugins, main


def cmd():
    try:
        import colorama
    except ImportError:
        pass
    else:
        colorama.init()

    plugin_list = load_plugins()
    exit_code = run_with_plugins(plugin_list)
    sys.exit(exit_code)


if __name__ == "__main__":
	cmd()
