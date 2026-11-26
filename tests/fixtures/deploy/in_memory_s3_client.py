import io


class InMemoryS3Client:
    """Stands in for the boto3 S3 client with a dictionary of objects, raising NoSuchKey
    the way boto3 does, so DeploymentRecorder can be checked without AWS."""

    class exceptions:
        class NoSuchKey(Exception):
            pass

    def __init__(self) -> None:
        self.objects = {}

    def get_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise self.exceptions.NoSuchKey(Key)
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objects[(Bucket, Key)] = Body

    def list_objects_v2(self, Bucket, Prefix):
        return {"Contents": [{"Key": key} for bucket, key in sorted(self.objects) if bucket == Bucket and key.startswith(Prefix)]}
