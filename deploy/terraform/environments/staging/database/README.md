# staging/database

PostgreSQL 17 on RDS for staging, in the private subnets of `staging/vpc/eu-central-1`. Multi-AZ, 14 days of point-in-time backups, a final snapshot and deletion protection. The server migrates the schema when it starts; in staging and prod the deployment snapshots the instance first.
