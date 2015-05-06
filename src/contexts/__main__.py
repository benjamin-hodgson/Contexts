import sys
from .plugin_discovery import load_plugins
from . import run_with_plugins


def cmd():
    if '--version' in sys.argv:
        print_version()
        sys.exit(0)

    try:
        import colorama
    except ImportError:
        pass
    else:
        colorama.init()

    plugin_list = load_plugins()
    exit_code = run_with_plugins(plugin_list)
    sys.exit(exit_code)


def print_version():
    import pkg_resources
    version = pkg_resources.require('contexts')[0].version
    py_version = '.'.join(str(i) for i in sys.version_info[0:3])

    print("Contexts version " + version)
    print("Running on Python version " + py_version)


if __name__ == "__main__":
    cmd()
