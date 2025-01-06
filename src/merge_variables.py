import logging
import os
import duckdb
import hydra
import pandas as pd

logger = logging.getLogger(__name__)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg):
    # == concat the df's ==    
    all_vars_list = []
    for variable in cfg.variables.names.keys():
        var_df = pd.read_parquet(
            f"data/input/{cfg.geo_type}__{cfg.survey}__{variable}.parquet"
        )
        all_vars_list.append(var_df)
    all_vars_df = pd.concat(all_vars_list, axis=1)

    # == save parquet ==
    all_vars_df.reset_index(inplace=True)
    con = duckdb.connect()
    con.register("all_vars", all_vars_df)

    for year in cfg.variables.valid_years[cfg.geo_type][cfg.survey]:
        os.makedirs(f"data/output/{cfg.geo_type}_yearly", exist_ok=True)
        filename = f"data/output/{cfg.geo_type}_yearly/{cfg.survey}_{year}.parquet"
        con.execute(f"""
            COPY (
                SELECT * 
                FROM all_vars 
                WHERE year = {year}
            ) 
            TO '{filename}' (FORMAT PARQUET)
        """)
        logger.info(f"GENERATED file {filename}")


if __name__ == "__main__":
    main()
