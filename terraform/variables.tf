variable "data_lake_bucket" {
  description = "GCP Bucket for Landsat image subsets"
}

variable "project" {
  description = "GCP Project ID"
}

variable "region" {
  description = "Region for GCP resources."
  default = "northamerica-northeast1"
  type = string
}

variable "storage_class" {
  description = "Storage class type for bucket. Check official docs for more info."
  default = "STANDARD"
}

variable "BQ_DATASET" {
  description = "BigQuery Dataset that raw data (from GCS) will be written to"
  type = string
  default = "landsat_data"
}
