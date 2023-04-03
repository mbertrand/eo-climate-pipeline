import os
from datetime import datetime, timedelta
from json import load
from pathlib import Path

import boto3
import rasterio as rio
from prefect_gcp.cloud_storage import GcsBucket
from pyproj import Transformer
from pystac_client import Client
from rasterio.features import bounds

from prefect import flow, task

STUDY_AREAS = [
    "saguaro_np_east.json",
    "saguaro_np_west.json",
    "pusch_ridge_north.json",
    "mt_wrightson_south.json",
]


def write_gcs(path: Path) -> None:
    """Upload local image subsets to GCS data lake"""
    gcs_block = GcsBucket.load("eo-climate-gcs")
    gcs_block.upload_from_path(from_path=path, to_path=path)
    return


def write_subset(
    study_area: str, band_name: str, geotiff_url: str, bbox: object, date: str
):
    """
    Extract a subset of a COG getiff and save locally
    """
    aws_session = rio.session.AWSSession(boto3.Session(), requester_pays=True)
    with rio.Env(aws_session):
        with rio.open(geotiff_url) as landsat_tif:
            # Calculate pixels in bbox
            transformer = Transformer.from_crs("epsg:4326", landsat_tif.crs)
            lat_north, lon_west = transformer.transform(bbox[3], bbox[0])
            lat_south, lon_east = transformer.transform(bbox[1], bbox[2])
            x_top, y_top = landsat_tif.index(lat_north, lon_west)
            x_bottom, y_bottom = landsat_tif.index(lat_south, lon_east)
            window = rio.windows.Window.from_slices(
                (x_top, x_bottom), (y_top, y_bottom)
            )

            # request this bbox subset from the cog geotiff on s3
            subset = landsat_tif.read(1, window=window)
            profile = landsat_tif.profile
            basename, ext = os.path.splitext(geotiff_url.split("/")[-1])
            year = date[:4]
            month = date[5:7]
            path = Path(
                f"landsat/{study_area}/{year}/{month}/{basename[:37]}/{band_name}{ext.lower()}"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            with rio.open(path, "w", **profile) as dst:
                dst.write(subset, 1)
        return path


@task(retries=3, retry_delay_seconds=4)
def process_images(
    study_area: str, images: list[dict], bands: list[str], bbox: tuple[float]
):
    """Save images for each band to the data lake"""
    for image in images:
        date = image["properties"]["datetime"][0:10]
        for band in bands:
            band_s3_url = image["assets"][band]["alternate"]["s3"]["href"]
            path = write_subset(study_area, band, band_s3_url, bbox, date)
            write_gcs(path)
            path.unlink()


@task(retries=3)
def get_landsat_data(geometry: dict, start_dt: str, end_dt: str, query=None):
    """Retrieve a list of landsat images matching the criteria"""
    landsat_STAC = Client.open("https://landsatlook.usgs.gov/stac-server", headers=[])
    landsat_search = landsat_STAC.search(
        intersects=geometry,
        datetime=f"{start_dt}/{end_dt}",
        query=query,
        collections="landsat-c2l2-sr",
    )
    return [item.to_dict() for item in landsat_search.get_items()]


@flow(log_prints=True)
def landsat_parent_flow(
    bands: list[str] = None,
    geojson_files: list[str] = None,
    start_date: str = None,
    end_date: str = None,
    query: dict = None,
):
    """Run get_landsat_data for each study area json file"""
    today = datetime.today()
    if not geojson_files:
        geojson_files = STUDY_AREAS
    if not bands:
        bands = ["red", "nir08", "qa_pixel"]
    if not start_date:
        start_date = (today - timedelta(days=14)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")

    for geojson_file in geojson_files:
        with open(f"geojson/{geojson_file}", "r") as geojson_inf:
            geojson_content = load(geojson_inf)
        study_area = Path(geojson_file).stem
        geometry = geojson_content["features"][0]["geometry"]
        bbox = bounds(geometry)
        images = get_landsat_data(geometry, start_date, end_date, query=query)
        print(
            f"Found {len(images)} Landsat images between {start_date}-{end_date} for {study_area}"
        )
        process_images.submit(study_area, images, bands, bbox)


if __name__ == "__main__":
    landsat_parent_flow()
