import unittest

if __name__ == "__main__":
    unittest.main(
        module="sandpiper.tests",
        verbosity=2,
        # Print warnings to stderr
        warnings='default',
        # Buffer stdout and stderr. If the test fails, the buffers will be
        # printed, otherwise they are discarded
        buffer=True
    )
