# Backend
Acts at the backend for UWPath. 

## Set up
Please refer to [Wiki](https://github.com/UW-Path/Backend/wiki/Developer:-Set-Up) for instructions to set up restful API

## Accesing prototype
A prototype is built with Django. To access the prototype, please pull the [website](https://github.com/UW-Path/Backend/tree/django_website) branch. 

## Versioned catalog artifacts

The backend can serve immutable catalog releases produced by the DataParsing
pipeline. Set `UWPATH_CATALOG_ROOT` to the directory containing academic-year
subdirectories such as `2026-2027/`. Optionally set
`UWPATH_ACTIVE_ACADEMIC_YEAR`; otherwise `active` resolves to the latest year.

The additive API does not change the existing database-backed endpoints when
no catalog root is configured:

- `GET /api/catalogs/`
- `GET /api/catalogs/active/`
- `GET /api/catalogs/<academic-year>/courses/`
- `GET /api/catalogs/<academic-year>/programs/`

Every release is checked against its manifest, SHA-256 hashes, record counts,
schema version, and publishability flag before it is served. Integrity failures
or missing configuration return a structured `503`; unknown years return `404`.

### Local catalog playground (no Oracle or Docker)

Point the backend at a DataParsing output directory and use the dedicated SQLite
settings module:

```sh
python3 -m venv .context/backend-venv
.context/backend-venv/bin/pip install -r requirements.txt

UWPATH_CATALOG_ROOT=/absolute/path/to/catalogs \
UWPATH_ACTIVE_ACADEMIC_YEAR=2026-2027 \
.context/backend-venv/bin/python manage.py runserver 127.0.0.1:8000 \
  --noreload --settings=uwpath_backend.catalog_settings
```

Then open <http://127.0.0.1:8000/api/catalogs/>. When a catalog root is set, the
legacy program, requirement, and course-info routes also read these files so the
existing frontend can run without Oracle. Structured course requirements are
translated conservatively; rules the legacy planner cannot represent are
reported in the response's `compatibility_warnings`. Prerequisite validation
still requires the legacy database.

In a Conductor workspace, link or copy catalogs to `.context/catalogs`, then use
the `catalog-api` run command. It binds to that workspace's allocated port.
