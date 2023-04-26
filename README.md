# Earth Observation: Normalized Difference Vegetation Index (NDVI) Pipeline

NDVI is a quantitative measurement derived from the red and near-infrared bands of satellite images.  It is useful as an indicator of vegetation density and drought conditions.

This demo data pipeline project extracts subsets of Landsat data within a specified date range across 4 regions surrounding Tucson, Arizona.  For each subsetted image, cloudy areas are masked out, the NDVI is calculated, and the mean NDVI per image is saved to a BigQuery database.
The dashboard below shows the mean NDVI over time from 2018 through early 2023 across the 4 study areas.

## Dashboard

The live dashboard is available at [this link](https://lookerstudio.google.com/reporting/f519ed16-b314-4720-a1e8-0bebc3724295).

![Screenshot 2023-04-03 at 8 28 12 AM](https://user-images.githubusercontent.com/187676/229644289-83521140-da3d-4265-a5a9-e25cd01c8aa5.png)


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
- Run `source .env`  
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
- Run each of the python files in the blocks folder.  
   ```
   python prefect/blocks/make_gcp_blocks.py
   python prefect/blocks/make_github_block.py
   ```

- Run the prefect pipelines, you can deploy them to the cloud and run from there:
  ```
  prefect deployment build  prefect/flows/aws_to_gcp_subset.py:landsat_parent_flow -n landsat_aws_to_gcp_subset -q default -sb github/eo-climate-github -a
  prefect deployment build  prefect/flows/gcp_cloudmask_ndvi.py:ndvi_parent_flow -n landsat_gcp_cloudmask_ndvi -q default -sb github/eo-climate-github -a
  prefect agent start -q 'default'
  ```
- or run locally:
  ```
  python prefect/flows/aws_to_gcp_subset.py
  python prefect/flows/gcp_cloudmask_ndvi.py
  ```
  
The `aws_to_gcp_subset.py` pipeline searches for Landsat satellite images covering the study area(s) within a specified time period and save the intersecting subset of each image to a data lake (Google Cloud bucket).

The `gcp_cloudmask_ndvi.py` pipeline masks out cloud cover in each image, calculates the NDVI from the red and near-infrared bands, and saved the mean NDVI per image in a BigQuery data warehouse.

You can schedule these to run automcatically in Prefect Cloud if you wish. You can adjust the date parameters either via the Prefect Cloud UI or by adjusting the default parameters in the python files.  


#### dnt
Follow [these instructions](https://docs.getdbt.com/docs/quickstarts/dbt-cloud/bigquery#connect-dbt-cloud-to-bigquery) to run the dbt scripts in the cloud, and as described in the [data engineering zoomcamp videos](https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/week_4_analytics_engineering#deploying-a-dbt-project).  You will need to fork this repo.

The dbt scripts transform the NDVI data from the BigQuery data warehouse, creating a new table free of duplicates, partitioned by date, and clustered by study area.  This table is used by the dashboard, which was created via Google's Looker Studio.
