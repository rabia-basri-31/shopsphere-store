import subprocess
import sys

SUITES = {
    "all": None,
    "m1": "m1",
    "m2": "m2",
    "m3": "m3",
    "unit": "unit",
    "route": "route",
    "security": "security",
    "boundary": "boundary",
    "smoke": "smoke",
}

USAGE = """usage: python run_tests.py [suite ...] [--parallel] [-- pytest options]

suites: {suites}

examples:
  python run_tests.py
  python run_tests.py m1
  python run_tests.py smoke
  python run_tests.py m1 m2 --parallel
  python run_tests.py security -- -x
""".format(suites=", ".join(SUITES))


def main():
    args = sys.argv[1:]

    extra = []
    if "--" in args:
        split = args.index("--")
        extra = args[split + 1:]
        args = args[:split]

    parallel = "--parallel" in args
    names = [arg for arg in args if arg != "--parallel"] or ["all"]

    unknown = [name for name in names if name not in SUITES]
    if unknown:
        print("unknown suite: " + ", ".join(unknown))
        print(USAGE)
        return 2

    command = [sys.executable, "-m", "pytest"]

    markers = [SUITES[name] for name in names if SUITES[name]]
    if "all" not in names and markers:
        command += ["-m", " or ".join(markers)]

    if parallel:
        command += ["-n", "auto", "--dist", "loadgroup"]

    command += extra
    print(" ".join(command))
    return subprocess.call(command)


if __name__ == "__main__":
    sys.exit(main())
