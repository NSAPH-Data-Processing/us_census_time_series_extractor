import logging

import duckdb
import hydra
import pandas as pd

logger = logging.getLogger(__name__)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg):
    # == concat the df's ==
    all_vars_list = []
    for variable in cfg.variable_codes.keys():
        var_df = pd.read_parquet(
            f"data/intermediate/census_variables/{cfg.geo_type}__{cfg.survey}__{variable}.parquet"
        )
        all_vars_list.append(var_df)
    all_vars_df = pd.concat(all_vars_list, axis=1)

    # == save parquet ==
    filename = f"data/output/census_series/{cfg.geo_type}__{cfg.survey}.parquet"
    con = duckdb.connect()
    all_vars_df.reset_index(inplace=True)
    con.register("all_vars", all_vars_df)
    con.execute(f"COPY all_vars TO '{filename}' (FORMAT PARQUET)")
    logger.info(f"GENERATED file {filename}")


if __name__ == "__main__":
    main()
