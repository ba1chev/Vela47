import json
from boto3.session import Session


def read_secret(secret_id: str, region: str) -> dict[str, str]:
    client = Session().client("secretsmanager", region_name = region)
    return json.loads(client.get_secret_value(SecretId = secret_id)["SecretString"])
