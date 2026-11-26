# dev/database

PostgreSQL 17 on RDS for dev, in the private subnets of `dev/vpc/eu-central-1`. Single-AZ, one day of backups and no final snapshot: dev data is disposable. The server migrates the schema when it starts; in staging and prod the deployment snapshots the instance first.
