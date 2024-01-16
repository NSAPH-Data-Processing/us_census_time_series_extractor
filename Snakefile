import yaml

# Load the YAML file
with open("conf/datapaths/datapaths.yaml", 'r') as file:
    datapaths_cfg = yaml.safe_load(file)

# Extract the first key under 'output'
output_folder = list(datapaths_cfg['output'].keys())[0]

# == Define rules ==

# rule all:
#     input:
#         expand("data/output/acs1_{geo_type}.csv", geo_type=["state", "county"]),
#         expand("data/output/acs5_{geo_type}.csv", geo_type=["state", "county", "zcta"]),
#         expand("data/output/sf1_{geo_type}.csv", geo_type=["state", "county"])

# Snakemake rules using the output folder
rule all:
    input:
        expand(f"data/output/{output_folder}/acs1_{{geo_type}}.csv", geo_type=["state", "county"]),
        expand(f"data/output/{output_folder}/acs5_{{geo_type}}.csv", geo_type=["state", "county", "zcta"]),
        expand(f"data/output/{output_folder}/sf1_{{geo_type}}.csv", geo_type=["state", "county"])


rule census_fetch_acs1:
    output:
        "data/output/{output_folder}/acs1_{geo_type}.csv"
    params:
        var_yaml = "census_acs1.yaml",
        table_name = "acs1"
    wildcard_constraints:
        geo_type = "state|county"
    shell:
        """
        python src/census_fetch.py --var_yaml {params.var_yaml} --geo_type {wildcards.geo_type} --census_type acs --table_name {params.table_name}
        """

rule census_fetch_acs5:
    output:
        "data/output/{output_folder}/acs5_{geo_type}.csv"
    params:
        var_yaml = "census_acs5.yaml",
        table_name = "acs5"
    wildcard_constraints:
        geo_type = "state|county|zcta"
    shell:
        """
        python src/census_fetch.py --var_yaml {params.var_yaml} --geo_type {wildcards.geo_type} --census_type acs --table_name {params.table_name}
        """

rule census_fetch_sf1:
    output:
        "data/output/{output_folder}/sf1_{geo_type}.csv"
    params:
        var_yaml = "census_dec.yaml",
        table_name = "sf1"
    wildcard_constraints:
        geo_type = "state|county|zcta"
    shell:
        """
        python src/census_fetch.py --var_yaml {params.var_yaml} --geo_type {wildcards.geo_type} --census_type dec --table_name {params.table_name}
        """
