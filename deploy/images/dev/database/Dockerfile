# The PostgreSQL the server uses in local development, in place of RDS. The database and
# its owner are fixed here and match the server's defaults; the password is handed in by
# Terraform as POSTGRES_PASSWORD. Connections are unencrypted, so the server runs with
# VELA47_DATABASE_SSL_MODE=disable against it.
FROM postgres:17-alpine

ENV POSTGRES_DB=vela47 \
    POSTGRES_USER=vela47
