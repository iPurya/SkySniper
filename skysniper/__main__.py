import sys

if __name__ == "__main__":
    # Check if the user is using the correct version of Python
    python_version = sys.version.split()[0]

    if sys.version_info < (3, 9):
        print(f"SkySniper requires Python 3.9+\nYou are using Python {python_version}, which is not supported by SkySniper.")
        sys.exit(1)

    from skysniper import skysniper
    skysniper.main()