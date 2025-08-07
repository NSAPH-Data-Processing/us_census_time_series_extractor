import hydra

conda: "requirements.yaml"
configfile: "conf/config.yaml"

envvars:  # this indicates environment vars that must be set, always done in docker
    "PYTHONPATH",
    "CENSUS_API_KEY",

with hydra.initialize(version_base=None, config_path="conf"):
    hydra_cfg = hydra.compose(config_name="config")

# == Obtain list of all target census variables (concepts) ==
variable_list = list(hydra_cfg.variables.names.keys())
print(variable_list)

# == Obtain output files from valid combinations of geo_types and surveys ===
merged_output_files = []
for geo_type in hydra_cfg.variables.valid_years.keys():
    for survey in hydra_cfg.variables.valid_years[geo_type].keys():
        for year in hydra_cfg.variables.valid_years[geo_type][survey]:
            merged_output_files.append(f"{cfg.datapaths.base_path}/output/{geo_type}_yearly/{survey}_{year}.parquet")
print(merged_output_files)

fetched_output_files = []
for geo_type in hydra_cfg.variables.valid_years.keys():
    for survey in hydra_cfg.variables.valid_years[geo_type].keys():
        for variable in variable_list:
            fetched_output_files.append(f"{cfg.datapaths.base_path}/input/{geo_type}__{survey}__{variable}.parquet")
print(fetched_output_files)

# == Define rules ==
rule all:
    input:
        merged_output_files,

rule fetch_variables:
    output:
        f"{cfg.datapaths.base_path}/input/{{geo_type}}__{{survey}}__{{variable}}.parquet",
    shell:
        """
        python src/fetch_variables.py \
            geo_type={wildcards.geo_type} \
            survey={wildcards.survey} \
            variable={wildcards.variable}
        """

rule merge_variables:
    input:
        fetched_output_files,
    output:
        merged_output_files,
    shell:
        """
        python src/merge_variables.py
        """

# TODO: investigate how to make a dynamic rule for the output as year depends on geo_type and survey
# rule merge_variables:
#     input:
#         expand(
#             "data/input/{{geo_type}}__{{survey}}__{var}.parquet",
#             var=variable_list,
#         ),
#     output:
#         "data/output/{geo_type}_yearly/{survey}_{year}.parquet"
#     shell:
#         """
#         python src/merge_variables.py
#         geo_type={wildcards.geo_type}
#         survey={wildcards.survey}
#         """
