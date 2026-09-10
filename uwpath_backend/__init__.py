"""UWPath backend package initialization."""

import os


if os.getenv("UWPATH_ENVIRONMENT"):
    import oracledb

    # Production historically used cx_Oracle and an auto-login wallet. Keep the
    # equivalent thick-mode behavior while using Django's supported driver.
    oracledb.init_oracle_client()
