FROM python:3.7
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE uwpath_backend.settings
WORKDIR /opt/oracle
RUN apt-get update && \
    apt-get install -y libaio1 unzip wget
RUN wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linuxx64.zip && \
    unzip instantclient-basiclite-linuxx64.zip && \
    rm -f instantclient-basiclite-linuxx64.zip && \
    cd instantclient* && \
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
EXPOSE 8000
