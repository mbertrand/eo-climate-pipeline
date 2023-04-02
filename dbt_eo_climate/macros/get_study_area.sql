
{#
    This macro returns a date
#}

{% macro get_study_area_title(study_area) -%}

    case {{ study_area }}
        when 'pusch_ridge_north' then 'Pusch Ridge (North)'
        when 'saguaro_np_east' then 'Saguaro National Park (East)'
        when 'saguaro_np_west' then 'Saguaro National Park (West)'
        when 'mt_wrightson_south' then 'My Wrightson (South)'
    end

{%- endmacro %}