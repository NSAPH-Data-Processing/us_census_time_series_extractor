import logging
import os
import duckdb
import hydra
import pandas as pd

logger = logging.getLogger(__name__)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg):
    # == concat the df's ==    
    for geo_type in cfg.variables.valid_years.keys():
        os.makedirs(f"{cfg.datapaths.base_path}/output/{geo_type}_yearly", exist_ok=True)
        for survey in cfg.variables.valid_years[geo_type].keys():
            all_vars_list = []
            for variable in cfg.variables.names.keys():
                var_df = pd.read_parquet(
                    f"{cfg.datapaths.base_path}/input/{geo_type}__{survey}__{variable}.parquet"
                )
                all_vars_list.append(var_df.set_index(["year", geo_type]))
            all_vars_df = pd.concat(all_vars_list, axis=1)

            # == save parquets ==
            all_vars_df.reset_index(inplace=True)
            con = duckdb.connect()
            con.register("all_vars", all_vars_df)

            for year in cfg.variables.valid_years[geo_type][survey]:
                filename = f"{cfg.datapaths.base_path}/output/{geo_type}_yearly/{survey}_{year}.parquet"
                con.execute(f"""
                    COPY (
                        SELECT * 
                        FROM all_vars 
                        WHERE year = {year}
                    ) 
                    TO '{filename}' (FORMAT PARQUET)
                """)
                logger.info(f"GENERATED file {filename}")
            con.close()

if __name__ == "__main__":
    main()
