FROM python:3.7

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE uwpath_backend.settings
WORKDIR /opt/oracle
RUN apt-get update && \
    apt-get install -y libaio1 unzip wget
RUN if [ $(uname -m) = "x86_64" ]; then \
        wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linuxx64.zip && \
        unzip instantclient-basiclite-linuxx64.zip && \
        rm -f instantclient-basiclite-linuxx64.zip; \
    elif [ $(uname -m) = "aarch64" ]; then \
        wget https://download.oracle.com/otn_software/linux/instantclient/191000/instantclient-basiclite-linux.arm64-19.10.0.0.0dbru.zip && \
        unzip instantclient-basiclite-linux.arm64-19.10.0.0.0dbru.zip && \
        rm -f instantclient-basiclite-linux.arm64-19.10.0.0.0dbru.zip; \
    fi
RUN cd instantclient*; \
    rm -f *jdbc* *occi* *mysql* *jar uidrvci genezi adrci && \
    echo /opt/oracle/instantclient* > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install psycopg2-binary==2.8.6
RUN pip install -r requirements.txt
COPY . /code/
ENV PATH /code/:$PATH
CMD python manage.py migrate && python manage.py runserver 0.0.0.0:8000
EXPOSE 8000
