{{ config(
   materialized='table',
   tags=["top-level"],
   partition_by={
       "field": "image_dt",
       "data_type": "date"
   },
   cluster_by=["study_area"]
)}}

with north_data as (
    select * 
    from {{ ref('stg_pusch_ridge_north') }}
), 

east_data as (
    select *
    from {{ ref('stg_saguaro_np_east') }}
), 

south_data as (
    select *
    from {{ ref('stg_mt_wrightson_south') }}
), 

west_data as (
    select *
    from {{ ref('stg_saguaro_np_west') }}
), 

ndvi_unioned as (
    select * from north_data
    union all
    select * from east_data
    union all
    select * from south_data
    union all
    select * from west_data
)

select 
    ndvi_unioned.image_id,
    ndvi_unioned.image_dt,
    cast ({{ get_study_area_title('ndvi_unioned.study_area') }} as string) as study_area,
    ndvi_unioned.ndvi_mean,
    ndvi_unioned.year,
    ndvi_unioned.month,
    cast(FORMAT_DATE("%Y-%m", image_dt) as string) as year_month
from ndvi_unioned