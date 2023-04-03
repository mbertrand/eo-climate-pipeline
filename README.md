# Earth Observation: Normalized Difference Vegetation Index (NDVI) Pipeline

NDVI is a quantitative measurement derived from the red and near-infrared bands of satellite images.  It is useful as an indicator of vegetation density and drought conditions.

This demo data pipeline project extracts subsets of Landsat data within a specified date range across 4 regions surrounding Tucson, Arizone.  For each subsetted image, cloudy areas are masked out, the NDVI is calculated, and the mean NDVI per image is saved to a BigQuery database.
The dashboard below shows the mean NDVI over time from 2018 through early 2023 across the 4 study areas.

## Dashboard

The live dashboard is available at [this link](https://lookerstudio.google.com/reporting/f519ed16-b314-4720-a1e8-0bebc3724295).

## How to run

#### Dependencies
Run the following:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

##### Terraform
- Set up a project in Google Cloud, create a service account for it, and generate/download keys in JSON format
  
- Create an .env file with the following:
   ```
   export TF_VAR_project=<your_project_name>
   export GOOGLE_APPLICATION_CREDENTIALS=<path/to/your service credentials json file>
   ```
- Authenticate with google cloud via the CLI
  ```
  gcloud auth application-default login
  ```  

- Go to the terraform folder and run:
  ```
  terraform apply
  ```

#### Prefect
- Login to Prefect Cloud (unless you want to run locally)
  - ```prefect cloud login``` 
- Run each of the python files in the blocks folder.  You can schedule these to run automcatically in Prefect Cloud if you wish. You can adjust the date parameters either via the Prefect Cloud UI or by adjusting the default parameters in the python files.
   ```
   cd prefect/blocks
   python make_gcp_blocks.py
   cd ../flows
   python aws_to_gcp_subset.py  # Downloads image subsets to data lake
   python gcp_cloudmask_ndvi.py # Masks image pixels w/cloud cover, calculates NDVI, saves image summary stats to BigQuery
   ```

###### DBT
Follow [these instructions](https://docs.getdbt.com/docs/quickstarts/dbt-cloud/bigquery#connect-dbt-cloud-to-bigquery) to run the dbt scripts in the cloud, and as described in the [data engineering zoomcamp videos](https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/week_4_analytics_engineering#deploying-a-dbt-project).  You will need to fork this repo.
