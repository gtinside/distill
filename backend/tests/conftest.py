import os

# The test suite authenticates via the X-User-Id header convenience, which is
# disabled in production. Enable it for tests only.
os.environ.setdefault("ALLOW_HEADER_AUTH", "1")
