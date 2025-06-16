import logging
import hydra
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def weighted_mean(values, weights):
    return np.average(values, weights=weights)

def weighted_sum(values, weights):
    return np.sum(values * weights)

@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg):
    # read in dec00 and acs09 file
    min_yr = cfg.interp.min_interp_year
    max_yr = cfg.interp.max_interp_year

    sp_res = cfg.interp.sp_res
    var_dict = cfg.variables.valid_years[sp_res]

    # construct survey dict
    # Start with dec years
    survey_dict = {yr: "dec" for yr in var_dict["dec"]}
    # Add acs5 years only if not already in the dict
    for yr in var_dict["acs5"]:
        if yr not in survey_dict:
            survey_dict[yr] = "acs5"

    df_start = pd.read_parquet(f"{cfg.interp.input_dir}/{survey_dict[min_yr]}_{min_yr}.parquet")
    df_end = pd.read_parquet(f"{cfg.interp.input_dir}/{survey_dict[max_yr]}_{max_yr}.parquet")

    year_lst = range(min_yr, max_yr+1)
    year_gap = len(year_lst)
    var_lst = list(cfg.variables.names.keys())

    # read in crosswalk file
    if cfg.interp.xwalk is not None:
        zcta_xwalk = pd.read_parquet(cfg.interp.xwalk.xwalk_fname)
        # merge with df_start
        df_start = df_start.merge(zcta_xwalk, left_on="zcta", right_on="zcta_00", how="inner")
        
        # Keep only necessary columns
        df_start = df_start[var_lst + ["weight", "zcta_10"]].copy()

        rate_vars = cfg.interp.xwalk.rate_vars
        count_vars = [v for v in var_lst if (v not in rate_vars)]

        # Calculate weighted means and sums using groupby
        # Use a list of aggregations for each variable
        agg_dict = {
            **{var: lambda x: weighted_mean(x, df_start.loc[x.index, "weight"]) for var in rate_vars},
            **{var: lambda x: weighted_sum(x, df_start.loc[x.index, "weight"]) for var in count_vars}
        }

        # Group by and aggregate in a single operation
        df_start = df_start.groupby("zcta_10").agg(agg_dict).reset_index()
        # merge in 2010 file
        df_mg = df_start.merge(df_end, left_on="zcta_10", right_on="zcta", how="inner", suffixes=("_start", "_end"))
    else:
        # otherwise match purely on same zctas, no xwalk
        df_mg = df_start.merge(df_end, on="zcta", how="inner", suffixes=("_start", "_end"))

    uniq_zcta = df_mg["zcta"].unique()

    # read in census variable
    var_diff = {}
    for var in var_lst:
        # make sure variable in both data frames
        if f"{var}_start" in df_mg.columns and f"{var}_end" in df_mg.columns:
            var_diff[var] = df_mg[f"{var}_end"] - df_mg[f"{var}_start"]
    

    for curr_step in range(year_gap):
        df_out = pd.DataFrame({var: df_mg[f"{var}_start"] + var_diff[var]/(year_gap - curr_step) for var in var_diff.keys()})
        df_out["zcta"] = df_mg["zcta"]
        df_out["year"] = int(year_lst[curr_step])
        df_out.to_parquet(f"{cfg.interp.out_dir}/{cfg.interp.base_name}__{year_lst[curr_step]}.parquet")

    if cfg.interp.export_diff is not None:
        var_diff["zcta"] = df_mg["zcta"]
        pd.DataFrame(var_diff).to_parquet(cfg.interp.export_diff)

    # additionally copying and editing filenames for more recent years
    for year in range(cfg.interp.max_interp_year, cfg.interp.max_census_year+1):
        df = pd.read_parquet(f"{cfg.interp.input_dir}/{survey_dict[year]}_{year}.parquet")

        # option to enforce constant zctas across all census files
        if cfg.interp.trim_zctas:
            df = df[df["zcta"].isin(uniq_zcta)]
        df.to_parquet(f"{cfg.interp.out_dir}/{cfg.interp.base_name}__{year}.parquet")


if __name__ == "__main__":
    main()
