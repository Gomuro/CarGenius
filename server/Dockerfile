FROM python:3.11.6-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /workdir_docker
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . /workdir_docker
CMD alembic upgrade head && pytest
EXPOSE 8000
