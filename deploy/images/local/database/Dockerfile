# The PostgreSQL the server uses in local development, in place of RDS. The database and
# its owner are fixed here and match the server's defaults; the password is handed in by
# Terraform as POSTGRES_PASSWORD. Connections are unencrypted, so the server runs with
# VELA47_DATABASE_SSL_MODE=disable against it.
# checkov:skip=CKV_DOCKER_2:Terraform gives the container its health check (modules/docker_database)
# checkov:skip=CKV_DOCKER_3:The PostgreSQL image drops to its postgres user itself
FROM postgres:17-alpine@sha256:f9cf3e1f0066f0eb0c48707d864f0ac5941e9ff454a072077d97a4d278d07d73

ENV POSTGRES_DB=vela47 \
    POSTGRES_USER=vela47
