{{ config(materialized="view")}}

with stg_mt_wrightson_south as
(
  select *,
    row_number() over(partition by SPLIT(image, '/')[OFFSET(5)]) as rn
  from {{ source('staging','ndvi_mt_wrightson_south') }}
  where SUBSTR(SPLIT(image, '/')[OFFSET(5)], 18) is not null and mean <= 1 and mean >= -1
)
select
    -- identifiers
    cast(CONCAT(study_area, '_', SPLIT(image, '/')[OFFSET(5)]) as string) as image_id,
    cast(SPLIT(image, '/')[OFFSET(5)] as string) as image_name,
    cast(study_area as string) as study_area,
    cast(CONCAT(year, '-', month, '-', SUBSTR(SPLIT(image, '/')[OFFSET(5)], 24, 2)) as date) as image_dt,
    cast(year as integer) as year,
    cast(month as integer) as month,
    cast(mean as float64)  as ndvi_mean,
    cast(pixel_count as integer) as pixel_count,
from stg_mt_wrightson_south
where rn = 1
order by year, month