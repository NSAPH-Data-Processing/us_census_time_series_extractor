import logging
import hydra
import pandas as pd

logger = logging.getLogger(__name__)

def weighted_mean(x, wt):
    return (x * wt).sum() / wt.sum()

@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg):
    # read in dec00 and acs09 file
    min_yr = cfg.interp.min_interp_year
    max_yr = cfg.interp.max_interp_year

    df_00 = pd.read_parquet(f"{cfg.interp.input_dir}/{cfg.interp.survey_dict[min_yr]}_{min_yr}.parquet")
    df_09 = pd.read_parquet(f"{cfg.interp.input_dir}/{cfg.interp.survey_dict[max_yr]}_{max_yr}.parquet")

    year_lst = range(min_yr, max_yr+1)
    year_gap = len(year_lst)
    var_lst = list(cfg.variables.names.keys())

    # read in crosswalk file
    if cfg.interp.intersect_files is not None:
        zcta_xwalk = pd.read_parquet(cfg.interp.intersect_files)
        # merge with df_00``
        df_00 = df_00.merge(zcta_xwalk, left_on="zcta", right_on="zcta_00", how="inner")
        
        # Keep only necessary columns
        df_00_2_10 = df_00[var_lst + ["weight", "zcta_10"]].copy()

        # Group and compute weighted mean
        df_00_2_10 = (
            df_00_2_10.groupby("zcta_10")
            .apply(lambda g: pd.Series({
                var: weighted_mean(g[var], g["weight"])
                for var in var_lst
            }))
            .reset_index()
        )
        # merge in 2010 file
        df_mg = df_00_2_10.merge(df_09, left_on="zcta_10", right_on="zcta", how="inner", suffixes=("_00", "_10"))
    else:
        # otherwise match purely on same zctas, no xwalk
        df_mg = df_00.merge(df_09, on="zcta", how="inner", suffixes=("_00", "_10"))

    uniq_zcta = df_mg["zcta"].unique()

    # read in census variable
    var_diff = {}
    for var in var_lst:
        # make sure variable in both data frames
        if f"{var}_00" in df_mg.columns and f"{var}_10" in df_mg.columns:
            var_diff[var] = df_mg[f"{var}_10"] - df_mg[f"{var}_00"]
    

    for curr_step in range(year_gap):
        df_out = pd.DataFrame({var: df_mg[f"{var}_00"] + var_diff[var]/(year_gap - curr_step) for var in var_diff.keys()})
        df_out["zcta"] = df_mg["zcta"]
        df_out["year"] = int(year_lst[curr_step])
        df_out.to_parquet(f"{cfg.interp.out_dir}/{cfg.interp.base_name}__{year_lst[curr_step]}.parquet")

    if cfg.interp.export_diff is not None:
        var_diff["zcta"] = df_mg["zcta"]
        pd.DataFrame(var_diff).to_parquet(cfg.interp.export_diff)

    # additionally copying and editing filenames for more recent years
    for year in range(cfg.interp.max_interp_year, cfg.interp.max_census_year+1):
        df = pd.read_parquet(f"{cfg.interp.input_dir}/{cfg.interp.survey_dict[year]}_{year}.parquet")
        if cfg.interp.trim_2010_yrs:
            df = df[df["zcta"].isin(uniq_zcta)]
        df.to_parquet(f"{cfg.interp.out_dir}/{cfg.interp.base_name}__{year}.parquet")


if __name__ == "__main__":
    main()
