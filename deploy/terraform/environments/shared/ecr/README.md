# shared/ecr

The repositories `vela47-app` and `vela47-sandbox`, shared by dev, staging and prod. The delivery workflow pushes each release once, tagged with its version; the environments run it by digest.

Applied once by hand after `shared/s3_state`.
