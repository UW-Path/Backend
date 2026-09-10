FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TNS_ADMIN=/code/Wallet_uwpathparallel \
    PATH=/code/:$PATH

WORKDIR /opt/oracle
RUN apt-get update \
    && apt-get install --no-install-recommends -y libaio1 unzip wget \
    && rm -rf /var/lib/apt/lists/*
RUN set -eux; \
    architecture="$(uname -m)"; \
    if [ "$architecture" = "x86_64" ]; then \
        client_url="https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linuxx64.zip"; \
    elif [ "$architecture" = "aarch64" ]; then \
        client_url="https://download.oracle.com/otn_software/linux/instantclient/191000/instantclient-basiclite-linux.arm64-19.10.0.0.0dbru.zip"; \
    else \
        echo "Unsupported architecture: $architecture" >&2; \
        exit 1; \
    fi; \
    wget --quiet "$client_url" -O instantclient.zip; \
    unzip -q instantclient.zip; \
    rm instantclient.zip; \
    find /opt/oracle -maxdepth 2 -type f \
        \( -name '*jdbc*' -o -name '*occi*' -o -name '*mysql*' -o -name '*.jar' \) \
        -delete; \
    echo /opt/oracle/instantclient* > /etc/ld.so.conf.d/oracle-instantclient.conf; \
    ldconfig

WORKDIR /code
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . ./
RUN python manage.py check \
    && chmod +x start.sh

CMD ["./start.sh"]
EXPOSE 8000
