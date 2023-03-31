{{ config(materialized="view")}}

with stg_push_ridge_north as
(
  select *, SUBSTR(SPLIT(image, '/')[OFFSET(5)], 18) as image_name,
    row_number() over(partition by image_name) as rn
  from {{ source('staging','ndvi_pusch_ridge_north') }}
  where image_name is not null
)
select
    -- identifiers
    image_name,
    cast(SUBSTR(image_name, 18, 8) as timestamp,
    cast(year as integer) as year,
    cast(month as integer) as month,
    cast(mean as numeric) as ndvi_mean,
    cast(min as numeric) as ndvi_min,
    cast(max as numeric) as ndvi_max,
    cast(pixel_count as integer) as pixel_count,
from stg_push_ridge_north
where rn = 1
-- dbt build --m <model.sql> --var 'is_test_run: false'
{% if var('is_test_run', default=false) %}
  limit 100
{% endif %}