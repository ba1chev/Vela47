import sys

from deploy.pipeline import ReleaseManifest

if __name__ == "__main__":
    print(ReleaseManifest.load().version)
    sys.exit(0)
