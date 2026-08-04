# Package Compatibility Notes

Checked on 2026-08-04 from the local development machine.

Local interpreter:

```text
Python 3.12.4
```

Python 3.8 dependency resolution was checked without installing packages:

```bash
python -m pip install --dry-run --ignore-installed --python-version 3.8 --only-binary=:all: -r requirements.txt
```

Result: pip resolved the pinned runtime dependencies for Python 3.8.

Important compatibility choices:

- `PyChromecast==12.1.4` is pinned because current `PyChromecast` releases
  require Python 3.11.
- `protobuf==3.20.3` is pinned because `PyChromecast==12.1.4` requires
  `protobuf<4`.
- `waitress==2.1.2` is pinned because current `waitress` releases require
  Python 3.9.
- `Flask==2.3.3` and related Pallets packages are pinned to avoid current
  releases that require Python 3.9.

