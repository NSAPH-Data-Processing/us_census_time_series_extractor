import pandas as pd
import duckdb
import hydra

@hydra.main(config_path="../conf", config_name="config_", version_base=None)
def main(cfg):
    # == concat the df's ==
    all_vars_list = []
    for variable in cfg.census.variables.keys():
        var_df = pd.read_parquet(f'data/intermediate/census_variables/{cfg.census.dataset_name}__{variable}.parquet')
        all_vars_list.append(var_df)
    all_vars_df = pd.concat(all_vars_list, axis=1)

    # == save parquet ==
    filename = f'data/output/census_series/{cfg.census.dataset_name}.parquet'
    con = duckdb.connect()
    con.register('all_vars', all_vars_df)
    con.execute(f"COPY all_vars TO '{filename}' (FORMAT PARQUET)")
    print(f"GENERATED file {filename}")

if __name__ == "__main__":
    main()