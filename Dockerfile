FROM python:3.8.2
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE uwpath_backend.settings
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
ENV PATH /code/:$PATH
EXPOSE 8000
