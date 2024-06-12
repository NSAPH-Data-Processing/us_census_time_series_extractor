import yaml

conda: "requirements.yaml"


configfile: "conf/config.yaml"


envvars:  # this indicates environment vars that must be set, always done in docker
    "PYTHONPATH",
    "CENSUS_API_KEY",


# == Obtain output files from valid combinations of geo_types and surveys ===
output_files = []
for geo_type in config["valid_years"].keys():
    for survey in config["valid_years"][geo_type].keys():
        output_files.append(f"data/output/census_series/{geo_type}__{survey}.parquet")

# == Obtain list of all target census variables (concepts) ==
variable_list = list(config["variable_codes"].keys())


# == Define rules ==
rule all:
    input:
        output_files,


rule fetch_variables:
    output:
        "data/intermediate/census_variables/{geo_type}__{survey}__{variable}.parquet",
    shell:
        """
        python src/fetch_variables.py \
            geo_type={wildcards.geo_type} \
            survey={wildcards.survey} \
            variable={wildcards.variable}
        """


rule merge_variables:
    input:
        expand(
            "data/intermediate/census_variables/{{geo_type}}__{{survey}}__{var}.parquet",
            var=variable_list,
        ),
    output:
        "data/output/census_series/{geo_type}__{survey}.parquet",
    shell:
        """
        python src/merge_variables.py \
            geo_type={wildcards.geo_type} \
            survey={wildcards.survey}
        """
