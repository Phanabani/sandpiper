import sys
from typing import Optional

import pytest
import yappi


def print_all(stats, out=sys.stdout, limit: Optional[int] = 10):
    if stats.empty():
        return
    columns = [
        ("name", 128),
        ("ncall", 10),
        ("ttot", 8),
        ("tsub", 8),
        ("tavg", 8),
    ]
    for name, length in columns:
        # noinspection PyStringFormat
        print(f"%-{length+2}s" % name, end="", file=out)
    print("", file=out)

    columns = {idx: i for idx, i in enumerate(columns)}
    if limit:
        stats = stats[:limit]
    for stat in stats:
        stat._print(out, columns)


def filter_callback(fn_stat: yappi.YFuncStat):
    return (
        "pytest" not in fn_stat.module
        and "pluggy" not in fn_stat.module
        and "mock" not in fn_stat.module
    )


def main(test_module: str, test_name: Optional[str] = None, sort_type: str = "ttot"):
    yappi.set_clock_type("WALL")
    with yappi.run():
        pytest_args = ["--pyargs", test_module]
        if test_name is not None:
            pytest_args += ["-k", test_name]
        pytest.main(pytest_args)
    fn_stats = yappi.get_func_stats(filter_callback=filter_callback)
    fn_stats.sort(sort_type)
    print("\n==== Profiling stats ====\n")
    print_all(fn_stats, limit=40)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "-h":
        print("Usage: " "yappi_profile_tests.py [test_module] [test_name] [sort_type]")
    elif 2 <= len(sys.argv) <= 4:
        main(*sys.argv[1:])
    else:
        main("sandpiper")
