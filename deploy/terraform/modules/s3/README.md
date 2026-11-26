# s3

A private S3 bucket for build output: the release artifacts of the delivery workflow and the deployment records of the deployment workflow. It is versioned, encrypted, reachable only over TLS, and blocks every public access. Overwritten versions expire after `noncurrent_version_expiration_days`. Objects under `expiring_prefixes` expire after `expiration_days`.

<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
