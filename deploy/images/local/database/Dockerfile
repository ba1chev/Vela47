# The PostgreSQL the server uses in local development, in place of RDS. The database and
# its owner are fixed here and match the server's defaults; the password is handed in by
# Terraform as POSTGRES_PASSWORD. Connections are unencrypted, so the server runs with
# VELA47_DATABASE_SSL_MODE=disable against it.
# checkov:skip=CKV_DOCKER_2:Terraform gives the container its health check (modules/docker_database)
# checkov:skip=CKV_DOCKER_3:The PostgreSQL image drops to its postgres user itself
FROM postgres:18-alpine@sha256:0115267ab5a509022df9319c77be365cef335adb71556c75f60f5360ee247e71

ENV POSTGRES_DB=vela47 \
    POSTGRES_USER=vela47
