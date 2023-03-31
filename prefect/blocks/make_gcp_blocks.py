
import os
from prefect_gcp import GcpCredentials
from prefect_gcp.cloud_storage import GcsBucket
import json

# alternative to creating GCP blocks in the UI
# insert your own service_account_file path or service_account_info dictionary from the json file
# IMPORTANT - do not store credentials in a publicly available repository!
credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
with open(credentials_path, "r") as inf:
    credentials_block = GcpCredentials(
        service_account_info=json.load(inf)  # enter your credentials info or use the file method.
    )
    credentials_block.save("eo-climate-gcp-creds", overwrite=True)


bucket_block = GcsBucket(
    gcp_credentials=GcpCredentials.load("eo-climate-gcp-creds"),
    bucket=f"{os.environ.get('TF_VAR_data_lake_bucket')}_{os.environ.get('TF_VAR_project')}",  # insert your  GCS bucket name
)

bucket_block.save("eo-climate-gcs", overwrite=True)

