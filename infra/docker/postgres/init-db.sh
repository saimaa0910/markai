#!/bin/bash
set -e

# Create databases if they don't exist
for db in eaimos_local eaimos_test; do
  if ! psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$db"; then
    echo "Creating database $db..."
    psql -U "$POSTGRES_USER" -c "CREATE DATABASE $db;"
  fi
done

# Enable extensions in all three databases
for db in eaimos eaimos_local eaimos_test; do
  echo "Enabling extensions in database $db..."
  psql -U "$POSTGRES_USER" -d "$db" -c "CREATE EXTENSION IF NOT EXISTS vector;"
  psql -U "$POSTGRES_USER" -d "$db" -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
  psql -U "$POSTGRES_USER" -d "$db" -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
  psql -U "$POSTGRES_USER" -d "$db" -c "CREATE EXTENSION IF NOT EXISTS unaccent;"
done
