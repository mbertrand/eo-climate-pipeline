import os
import re
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import rasterio as rio
import unpackqa
from dateutil.relativedelta import relativedelta
from prefect_gcp import GcpCredentials
from prefect_gcp.cloud_storage import GcsBucket

from prefect import flow, task

STUDY_AREAS = [
    "saguaro_np_east",
    "saguaro_np_west",
    "pusch_ridge_north",
    "mt_wrightson_south",
]

LandsatNDVIData = namedtuple(
    "LandsatNDVIData",
    ["study_area", "year", "month", "mean", "min", "max", "pixel_count", "image"],
)


@task()
def write_gcs(path: Path) -> None:
    """Upload local NDVI image subsets to GCS"""
    gcs_block = GcsBucket.load("eo-climate-gcs")
    gcs_block.upload_from_path(from_path=path, to_path=path)
    return


@task()
def write_bq(df: pd.DataFrame, project_id: str, study_area: str) -> None:
    """Write DataFrame containing NDVI summary stats to BiqQuery"""

    gcp_credentials_block = GcpCredentials.load("eo-climate-gcp-creds")

    df.to_gbq(
        destination_table=f"landsat_data.ndvi_{study_area}",
        project_id=project_id,
        credentials=gcp_credentials_block.get_credentials_from_service_account(),
        chunksize=500_000,
        if_exists="append",
    )


@task(retries=3)
def get_image_folders_from_gcs(study_area: str, year: int, month: int) -> Path:
    """Get landsat image folders from the data lake for the specified study area, month, year"""
    gcs_path = f"landsat/{study_area}/{year}/{str(month).zfill(2)}"
    gcs_block = GcsBucket.load("eo-climate-gcs")
    bucket_name = gcs_block.get_bucket().name
    return [f"{bucket_name}/{path}" for path in gcs_block.list_folders(gcs_path)]


@task(retries=3)
def process_image_set(image_path: str):
    """
    Calculate NDVI and summary statistics for the specified image path
    """
    out_img = f"processed/{'/'.join(image_path.split('/')[1:])}/masked_ndvi.tif"
    gcp_credentials_block = GcpCredentials.load("eo-climate-gcp-creds")
    gcp_session = rio.session.GSSession(
        google_application_credentials=gcp_credentials_block.service_account_file
    )
    with rio.Env(gcp_session):
        with rio.open(f"gs://{image_path}/red.tif") as red_img:
            red_data = red_img.read(1)
            profile = red_img.profile.copy()
            profile.update({"dtype": "float32", "nodata": 0.0})
        with rio.open(f"gs://{image_path}/nir08.tif") as nir_img:
            nir_data = nir_img.read(1)
        with rio.open(f"gs://{image_path}/qa_pixel.tif") as qa_img:
            qa = qa_img.read(1)
        cloud_only_mask = unpackqa.unpack_to_array(
            qa, product="LANDSAT_8_C2_L2_QAPixel", flags=["Cloud"]
        )

        ndvi = (nir_data - red_data) / (nir_data + red_data)
        ndvi_masked = np.ma.masked_array(ndvi, mask=cloud_only_mask)

        """
        Uncomment the following lines if you wish to save NDVI images to your Google Cloud bucket
        """
        # Path(out_img).parent.mkdir(parents=True, exist_ok=True)
        # with rio.open(out_img, "w", **profile) as dest:
        #     dest.write(ndvi_masked, 1)

        return (
            out_img,
            np.mean(ndvi_masked),
            np.min(ndvi_masked),
            np.max(ndvi_masked),
            np.count_nonzero(~np.isnan(ndvi_masked)),
        )


@flow(log_prints=True)
def calculate_ndvi(
    study_area: str, start_date: datetime, end_date: datetime, project_id: str
):
    """
    Calculate NDVI for images within the specified study area and date range.
    """
    print(f"Calculcate NDVI for {study_area}, {start_date} to {end_date}")

    current_date = start_date
    ndvi_data = []
    while current_date <= end_date:
        image_paths = get_image_folders_from_gcs(
            study_area, current_date.year, current_date.month
        )
        print(f"Found these image paths: {image_paths}")
        for image_path in image_paths:
            image_path_date = re.findall(r".\w{4}_\w{4}_\d{6}_(\d{8})", image_path)
            if (
                image_path_date
                and start_date
                <= datetime.strptime(image_path_date[0], "%Y%m%d")
                <= end_date
            ):
                print(f"Processing image {image_path}")
                (
                    ndvi_image_path,
                    ndvi_mean,
                    ndvi_min,
                    ndvi_max,
                    ndvi_pixels,
                ) = process_image_set(image_path)
                print(f"Mean NDVI for {ndvi_image_path} is {ndvi_mean}")
                if ndvi_mean > 0:
                    # write_gcs(ndvi_image_path)
                    # Path(ndvi_image_path).unlink()
                    ndvi_data.append(
                        LandsatNDVIData(
                            study_area,
                            current_date.year,
                            current_date.month,
                            ndvi_mean,
                            ndvi_min,
                            ndvi_max,
                            ndvi_pixels,
                            ndvi_image_path,
                        )
                    )
            else:
                print(f"Skipping {image_path}")
        current_date = current_date + relativedelta(months=1)
        print(f"NDVI DATA IS {ndvi_data}")
        write_bq.submit(pd.DataFrame(data=ndvi_data), project_id, study_area)


@flow(log_prints=True)
def ndvi_parent_flow(
    study_areas: List[str] = None,
    start_date: str = None,
    end_date: str = None,
    project_id: str = None,
):
    """
    Calculate NDVI for images in a list of study areas within the specified date range.
    """
    today = datetime.today()
    if not project_id:
        project_id = os.environ.get("TF_VAR_project", "mattsat")
    if not study_areas:
        study_areas = STUDY_AREAS

    if not start_date:
        start_date = today - relativedelta(days=14)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if not end_date:
        end_date = today
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    for study_area in study_areas:
        calculate_ndvi(study_area, start_date, end_date, project_id)


if __name__ == "__main__":
    ndvi_parent_flow()
