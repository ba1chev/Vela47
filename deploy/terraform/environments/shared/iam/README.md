# shared/iam

The permissions of `vela47-role`, the role the workflows assume, and the permissions boundary of every role the pipeline creates. Applied by hand with your own credentials, never by the pipeline: the CI policy denies the role any change to itself, its policy or the boundary, so its permissions only grow through a pull request and this apply.

Apply after `shared/s3_state` and before the first deployment. The role and the GitHub identity provider must already exist (see `docs/open_id_connect.md`).
