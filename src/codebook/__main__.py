"""Entry point for python -m codebook.

Note: On Python 3.13+ with free-threaded builds, you may see a RuntimeWarning
about watchdog and the GIL. This is harmless - watchdog works correctly.
To suppress it, run with: python -W ignore::RuntimeWarning -m codebook ...
"""

from codebook.cli import main

if __name__ == "__main__":
    main()
