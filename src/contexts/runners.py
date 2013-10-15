from .builders import build_suite


def run(spec, result):
    suite = build_suite(spec)
    suite.run(result)
