import hydra

conda: "requirements.yaml"
configfile: "conf/config.yaml"

envvars:  # this indicates environment vars that must be set, always done in docker
    "PYTHONPATH",
    "CENSUS_API_KEY",

with hydra.initialize(version_base=None, config_path="conf"):
    hydra_cfg = hydra.compose(config_name="config")


# == Obtain output files from valid combinations of geo_types and surveys ===
output_files = []
for geo_type in hydra_cfg.variables.valid_years.keys():
    for survey in hydra_cfg.variables.valid_years[geo_type].keys():
        for year in hydra_cfg.variables.valid_years[geo_type][survey]:
            output_files.append(f"data/output/{geo_type}_yearly/{survey}_{year}.parquet")
print(output_files)

# == Obtain list of all target census variables (concepts) ==
variable_list = list(hydra_cfg.variables.names.keys())
print(variable_list)

# == Define rules ==
rule all:
    input:
        output_files,


rule fetch_variables:
    output:
        "data/input/{geo_type}__{survey}__{variable}.parquet",
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
            "data/input/{{geo_type}}__{{survey}}__{var}.parquet",
            var=variable_list,
        ),
    output:
        "data/output/{geo_type}_yearly/{survey}_{year}.parquet",
    shell:
        """
        python src/merge_variables.py \
            geo_type={wildcards.geo_type} \
            survey={wildcards.survey} \
            year={wildcards.year}
        """
