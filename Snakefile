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
variable_list = list(census_cfg.keys())
print(f"variable_list: {variable_list}")

# == Define rules ==
rule all:
    input:
        expand(f"data/intermediate/census_variables/{config['dataset_name']}__{{variable}}.parquet", 
            variable=variable_list
        )

rule fetch_variables:
    output:
        f"data/intermediate/census_variables/{config['dataset_name']}__{{variable}}.parquet"
    shell:
        f"""
        PYTHONPATH=. python src/fetch_variables.py variable={{wildcards.variable}} 
        """
