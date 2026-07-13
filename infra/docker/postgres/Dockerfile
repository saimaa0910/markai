FROM postgres:16-bookworm

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-16 \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --branch v0.7.0 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make clean \
    && make \
    && make install \
    && cd .. \
    && rm -rf pgvector
