

##### Terraform
- Set up a project in Google Cloud, create a service account for it, adn generate/download keys in JSON format
  
- Create an .env file with the following:
   ```
   export TF_VAR_project=mattsat
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

###### Initial setup
- Login to Prefect Cloud (unless you want to run locally)
  - ```prefect cloud login``` 
- Run each of the python files in the blocks folder.  You can schedule these to run automcatically in Prefect Cloud if you wish.
   ```
   python aws_to_gcp_subset.py  # Downloads image subsets to data lake
   python gcp_cloudmask_ndvi.py # Masks image pixels w/cloud cover, calculates NDVI, saves image summary stats to BigQuery
   ```

###### DBT
Run `dbt init`