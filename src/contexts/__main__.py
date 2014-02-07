from . import main


def cmd():
    try:
        import colorama
    except ImportError:
        pass
    else:
        colorama.init()

    main()


if __name__ == "__main__":
	cmd()
