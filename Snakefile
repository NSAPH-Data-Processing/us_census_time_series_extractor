import yaml

conda: "requirements.yaml"
configfile: "conf/config_.yaml"
envvars: # this indicates environment vars that must be set, always done in docker
    "PYTHONPATH",  
    "CENSUS_API_KEY"

# == Load configuration ==
# dynamic config files
defaults_dict = {key: value for d in config['defaults'] if isinstance(d, dict) for key, value in d.items()}
census_cfg = yaml.safe_load(open(f"conf/census/{defaults_dict['census']}.yaml", 'r'))
# == Define variables ==
variable_list = list(census_cfg['variables'].keys())
print(f"variable_list: {variable_list}")
dataset_name = census_cfg['dataset_name']
print(f"dataset_name: {dataset_name}")

# == Define rules ==
rule all:
    input:
        expand(f"data/intermediate/census_variables/{dataset_name}__{{variable}}.parquet", 
            variable=variable_list
        )

rule fetch_variables:
    output:
        f"data/intermediate/census_variables/{dataset_name}__{{variable}}.parquet"
    shell:
        f"""
        PYTHONPATH=. python src/fetch_variables.py variable={{wildcards.variable}} 
        """
