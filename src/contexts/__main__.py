from . import main
from .plugin_discovery import load_plugins


def cmd():
    try:
        import colorama
    except ImportError:
        pass
    else:
        colorama.init()

    main(None, load_plugins())


if __name__ == "__main__":
	cmd()
