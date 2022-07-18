FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install psycopg2-binary==2.8.6
RUN pip install -r requirements.txt
COPY . /code/
ENV PATH /code/:$PATH
EXPOSE 8000
