# core/utils.py
from google.cloud import secretmanager

def access_secret(project_id, secret_id, version_id="latest"):
    """
    Access a single secret version in Google Secret Manager.
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/1"#{version_id}"
    print(name)
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_secrets(project_id, secret_ids):
    """
    Retrieve multiple secrets.
    """
    secrets = {}
    for secret_id in secret_ids:
        secrets[secret_id] = access_secret_version(project_id, secret_id)
    return secrets
