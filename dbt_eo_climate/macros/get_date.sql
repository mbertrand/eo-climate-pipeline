
{#
    This macro returns a date
#}

{% macro get_date(year, month, image_name) -%}

CONCAT(year, '-', month, '-', SUBSTR(SPLIT(image, '/')[OFFSET(5)], 24, 2))

{%- endmacro %}