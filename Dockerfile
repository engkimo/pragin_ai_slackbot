# Base Image
FROM python:3.10

# Install dependencies
ENV LANG C.UTF-8 \
    LC_ALL C.UTF-8 \
    APP_ROOT=/app \
    PYTHONIOENCODING utf-8 \
    PYTHON_VERSION=3.10 \
    PYTHON_MAJOR=3.10 \
    PYTHONPATH="${PYTHONPATH}:${APP_ROOT}"

ENV PORT 3000

RUN \
    apt-get update -y \
    && apt-get install -y \
    curl \
    git \
    libzbar0 \
    mupdf \
    libzbar-dev \
    python3 \
    python3-dev \
    python3-pip \
    && pip3 install pip --upgrade \
    && pip3 install setuptools poetry

# Set the working directory
WORKDIR ${APP_ROOT}

# Install python packages
COPY . ${APP_ROOT}
RUN pip install --trusted-host pypi.python.org -r requirements.txt

ENTRYPOINT ["python3", "manage.py", "runserver", "0:8000", "--insecure"]

# ポート8000を公開
EXPOSE 8000