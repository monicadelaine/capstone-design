# pull base image
FROM python:3.11-slim

# set working directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install system dependencies
RUN apt-get update \
  && apt-get install -y --no-install-recommends netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*

# create a non-root user and group before installing anything app-related
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# install dependencies (still as root so pip can write globally)
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint and fix line endings, then make executable
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh \
  && chmod +x /usr/src/app/entrypoint.sh

# copy project and hand ownership to appuser
COPY . .
RUN chown -R appuser:appgroup /usr/src/app

# drop to non-root user for runtime
USER appuser

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
