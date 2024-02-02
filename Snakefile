rule all:
    input:
        expand("data/output/census_series/acs1_{geo_type}.parquet", geo_type=["state", "county"]),
        expand("data/output/census_series/acs5_{geo_type}.parquet", geo_type=["state", "county", "zcta"]),
        expand("data/output/census_series/sf1_{geo_type}.parquet", geo_type=["state", "county"])


rule census_fetch:
    output:
        "data/output/census_series/{census_type}_{geo_type}.parquet"
    shell:
        """
        python src/census_fetch.py geo_type={wildcards.geo_type} census={wildcards.census_type}
        """
