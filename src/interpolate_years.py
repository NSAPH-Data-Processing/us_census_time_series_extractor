import duckdb
import pandas as pd
import numpy as np
import hydra
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def align_basis(
    df: pd.DataFrame,
    xwalk: pd.DataFrame,
    on: str,                 # column in df that matches the xwalk "from" ids
    from_colname: str,       # source id column in xwalk
    to_colname: str,         # target id column in xwalk
    value_col: str,  # the numeric column to align
    weight_col: str,  # weights in xwalk
    groupby_cols: list[str] | None = None,  # e.g., ["year"]
    #keep_unmatched: bool = False            # keep rows that don't hit the crosswalk
) -> pd.DataFrame:
    """Aligns a DataFrame to a new basis using a crosswalk DataFrame."""

    # Merge df to xwalk
    merged = df.merge(
        xwalk[[from_colname, to_colname, weight_col]],
        left_on=on,
        right_on=from_colname,
        how="left"
    )

    # Contribution
    merged["_contrib_"] = merged[value_col] * merged[weight_col]

    # Build grouping: user-specified + target id
    group_keys = (groupby_cols or []) + [to_colname]

    # Aggregate
    out = (
        merged.groupby(group_keys, dropna=False)["_contrib_"]
        .sum()
        .reset_index()
        .rename(columns={"_contrib_": value_col, to_colname: on})
    )

    return out

def interpolate_years(df: pd.DataFrame, id_name: str, var_name: str):
    min_year, max_year = df["year"].min(), df["year"].max()
    logger.info(f"Year range for {var_name}: {min_year} - {max_year}")
    
    all_years = list(range(min_year, max_year + 1))
    
    def interpolate_group(group):
        valid = group[var_name].notna() 
        
        if valid.sum() < 1:
            y_interp = np.full(len(all_years), np.nan)
        else:
            y_interp = np.interp(all_years, group.loc[valid, 'year'], group.loc[valid, var_name])

        # Create DataFrame with interpolated values and copy constant columns
        result = pd.DataFrame({'year': all_years, var_name: y_interp})
        for col in group.columns:
            if col not in ('year', var_name):
                result[col] = group.iloc[0][col]
        
        return result
    
    return df.groupby(id_name).apply(interpolate_group).reset_index(drop=True) #DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.


@hydra.main(config_path="../conf", config_name="interp", version_base=None)
def main(cfg):
    
    conf_interp = cfg.interp[cfg.geo_type]
    
    for target_basis in conf_interp.intervals.keys():
        logger.info(f"Processing target basis: {target_basis}")

        all_vars_df_list = []

        for var in cfg.variables.names.keys():
            logger.info(f"Processing variable: {var}")

            time_series_dict = {}
            
            for survey in conf_interp.intervals[target_basis].keys():
                for year in conf_interp.intervals[target_basis][survey]:
                    
                    if time_series_dict.get(year) is not None:
                        # error: there most only be a single datapoint per year
                        raise ValueError(f"Multiple datapoints found for {year}")
                    #TODO: implement multiple datapoints handling

                    input_file = f"{cfg.datapaths.base_path}/input/{cfg.geo_type}__{survey}__{var}.parquet"
                    time_series_dict[year] = duckdb.sql(f"""
                        SELECT 
                          {cfg.geo_type},
                          year,
                          {var}
                        FROM '{input_file}'
                        WHERE year = {year}
                    """).fetchdf()
                    
                    logger.info(f"{survey} {year} rows: {len(time_series_dict[year])}")

                    xwalk_name = conf_interp.align.get(target_basis, {}).get(survey, {}).get(year)
                    if xwalk_name is not None:
                        
                        xwalk_file = f"{cfg.datapaths.base_path}/xwalk/zcta/{cfg.xwalks[xwalk_name].file}"
                        xwalk = pd.read_parquet(xwalk_file)
                        from_colname = cfg.xwalks[xwalk_name].from_colname
                        to_colname = cfg.xwalks[xwalk_name].to_colname
                        
                        time_series_dict[year] = align_basis(
                            time_series_dict[year], 
                            xwalk,
                            on=cfg.geo_type,
                            from_colname=from_colname,
                            to_colname=to_colname,
                            value_col=var,
                            weight_col=cfg.xwalks[xwalk_name].weights_colname,
                            groupby_cols=["year"]
                        )
                        
                        logger.info(f"from zctas: {len(np.unique(xwalk[from_colname]))}")
                        logger.info(f"to zctas: {len(np.unique(xwalk[to_colname]))}")
                        logger.info(f"{survey} {year} rows: {len(time_series_dict[year])}")

            time_series_df = pd.concat(time_series_dict.values(), ignore_index=True)

            time_series_df = interpolate_years(
                df=time_series_df,
                id_name=cfg.geo_type,
                var_name=var
            )

            all_vars_df_list.append(time_series_df.set_index([cfg.geo_type, "year"]))

        # save year output files
        all_vars_df = pd.concat(all_vars_df_list, axis=1)
        all_vars_df.reset_index(inplace=True)
        
        years = all_vars_df["year"].unique()
        for year in years:
            output_file = f"{cfg.datapaths.base_path}/output/{cfg.interp[cfg.geo_type].output_prefix}_{year}.parquet"
            duckdb.sql(f"""
                COPY (
                    SELECT * FROM all_vars_df
                    WHERE year = {year}
                ) TO '{output_file}' (FORMAT 'parquet');
            """)
            logger.info(f"Output written to: {output_file}")

if __name__ == "__main__":
    main()