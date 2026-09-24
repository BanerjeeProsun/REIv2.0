import sys
import time

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "crash":
        sys.exit(1)

    # Just sleep until killed
    while True:
        time.sleep(1)
