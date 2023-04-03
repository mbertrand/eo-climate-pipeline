
{#
    This macro returns a date
#}

{% macro get_study_area_title(study_area) -%}

    case {{ study_area }}
        when 'pusch_ridge_north' then 'Pusch Ridge (North)'
        when 'saguaro_np_east' then 'Saguaro National Park (East)'
        when 'saguaro_np_west' then 'Saguaro National Park (West)'
<<<<<<< HEAD
        when 'mt_wrightson_south' then 'Mt. Wrightson (South)'
=======
        when 'mt_wrightson_south' then 'My Wrightson (South)'
>>>>>>> e8eaae7f6819cb415f82863ceb154f37b6a9bd4b
    end

{%- endmacro %}