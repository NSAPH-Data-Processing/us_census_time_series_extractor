[![](<https://img.shields.io/badge/Dataverse-10.7910/DVN/SYNPBS-orange>)](https://doi.org/10.7910/DVN/N3IEXS)

# US Census Bureau Time Series Extractor

This repository streamlines the extraction of time series from American Community Survey 5-Year Data (ACS5), American Community Survey 1-Year Data (ACS1) and Decennial Census (SF1). 

- **Extraction** : We leverage the Census API to efficiently extract data.

- **Processing & Final Dataset** : We transform the subset of variables obtained from the API and generate datasets of selected sociodemographic concepts.

The data is preprocessed to ensure consistency across years and geographies. Census variables are downloaded, cleaned (with invalid values converted to missing), and computed as counts or percentages according to configuration. Each variable is stored separately, then aligned to a common geographic basis using published crosswalks when boundaries change (if needed). Linear interpolation provides intermediate annual estimates without extrapolation. Finally, variables are merged into per-year, per-geography parquet files. The resulting outputs use standardized variable names ready for analysis.

### Scripts 

- `src/create_datapaths.py`: materializes directories/symlinks from `conf/datapaths/*`; ensures `data/<profile>/{input,output,xwalk}` exist.
- `src/fetch_variables.py`: selects dataset segments by `from_year`, fetches for `valid_years`, coerces to numeric, computes counts/percents, labels (`year`,`survey`), writes per-variable parquet under `data/<profile>/input/...`.
- `src/interpolate_years.py` (optional): composes sequences per `conf/interp/*:intervals`, applies crosswalks where `align` is defined, performs linear interpolation, generates `data/<profile>/output/<prefix>__<year>.parquet`.
- `src/merge_variables.py`: loads per-variable parquet for a `geo_type`+`survey`, aligns to `['year','survey',<geo>]`, merges columns, writes one parquet per year via DuckDB to `data/<profile>/output/<geo>_yearly/...`.


## Output File structure

Output file names determine the content

* acs5_<yyyy>.parquet contains values fetched from the API for the ac5 survey
* acs1_<yyyy>.parquet contains values fetched from the API for the acs1 survey
* dec_<yyyy>.parquet contains values fetched from the API for the dec survey
* demographics__census__core__zcta_yearly__<yyyy>.parquet interpolated series

Note: `<yyyy>` is the output year.

### Data Dictionary

`acs5_<yyyy>.parquet`, `acs1_<yyyy>.parquet`, and `dec_<yyyy>.parquet` contain the following columns. 

| Column Name| Description|
|---------------------------------|------------------------------------------------------------------------|
| `survey`| Type of survey, it takes one of the following values: dec, acs1, acs5|
| `year`| Year of the variable estimates.|
| geographic level| Id of geogragraphies at a given geographic level. The column name takes the name of the geographic level (zcta, county, state)|
| Various sociodemographic columns| Columns containing variables related to sociodemographic characteristics such as population distribution by age groups, ethnic composition, housing statistics, and other demographic and socioeconomic variables. The column name is the name of the variable|

`demographics__census__core__zcta_yearly__<yyyy>.parquet` does not contain the `survey` column because it contains time series estimates that pull data from multiple surveys.

## Data Lineage

The description of the data sources is included here:

**a) American Community Survey 5-Year Data (ACS5)**

- Estimates from samples obtained across 5 years.
- Time Coverage : 2009–2022 for counties and 2011–2022 for ZCTAs.
- Population: All 50 states including the District of Columbia, Puerto Rico, and other U.S. territories.
- Geographical Coverage: nation, all states (including DC and Puerto Rico), all metropolitan areas, all congressional districts (116th congress), all counties, all places, all tracts and block groups.
- ZCTA Coverage
- Data Source: The American Community Survey (ACS) is an ongoing survey that provides data every year -- giving communities the current information they need to plan investments and services. The ACS covers a broad range of topics about social, economic, demographic, and housing characteristics of the U.S. population.

**b) American Community Survey 1-Year Data (ACS1)**

- Time Coverage : 2005 - 2022
- Population: All 50 states including the District of Columbia, Puerto Rico, and other U.S. territories.
- Geographical Coverage: available for the nation, all 50 states, the District of Columbia, Puerto Rico, every congressional district, every metropolitan area, and all counties and places with populations of 65,000 or more.
- No ZCTA coverage
- Data Source: The American Community Survey (ACS) is an ongoing survey that provides data every year -- giving communities the current information they need to plan investments and services. The ACS covers a broad range of topics about social, economic, demographic, and housing characteristics of the U.S. population.

**c) Decennial Census**

- Time Coverage: For the years 2000, 2010, 2020
- Geographical Coverage: Summary File 1 (SF 1) is released as individual files for each of the 50 states, the District of Columbia, and
Puerto Rico, and for the United States.
- Data Source: Summary File 1 (SF 1) contains the data compiled from the questions asked of all people and about every housing unit. Population items include sex, age, race, Hispanic or Latino origin, household relationship, household type, household size, family type, family size, and group quarters.

## Processing Rules

**Processing rules**

ACS5 estimates represent estimates over 5-year periods, so how to map a single year to each value is not evident. Here we assign the **mid year of the 5-year period to the acs5 estimates**.

**American Community Survey 1-Year Data and Hispanic Variable**

Hispanic data was incorporated starting from the 2009 ACS 1-year estimates and hence not available for the years 20005-2008 for ACS 1-Year estimates.

## Repository Content

The repository contains: 

- [conf/](conf/): configuration files. 
- [src/fetch_variables.py](src/fetch_variables.py): the main script for querying Census API.
- [environment.yml](environment.yml): conda environment setup.

## Run

You can run the pipeline steps manually or run the snakemake pipeline described in the Snakefile.

**Run the pipeline steps manually to fetch a single variable**

The census variable codes that are used to create the time series are defined in the `yaml` file stored in `conf/variables/<config_yaml>`. The data paths attached to the pipeline are defined in `conf/datapaths/<config_yaml>`.

### Fix the key params in config
For example:
```
  - datapaths: datapaths
  - variables: core
```

```bash
# Create and activate the conda environment
conda env create -f requirements.yml
conda activate census_series

# Set your Census API key
export CENSUS_API_KEY='your_api_key_here'

# Create the data directory paths
python src/create_datapaths.py

# Execute the main script
PYTHONPATH=. python src/fetch_variables.py variable=pop_native geo_type=county survey=acs1
```

## Run snakemake pipeline

The pipeline is orchestrated by Snakemake and parameterized by Hydra configs.

Key components:
- `Snakefile`: defines high-level workflow rules.
- `src/create_datapaths.py`: creates local data directories and/or symlinks to shared storage as specified by configs.
- `src/fetch_variables.py`: fetches a single variable across valid years; writes parquet to `data/.../input/`.
- `src/interpolate_years.py`(optional step): aligns to a specified geographic basis (via crosswalks) and linearly interpolates to annual series; writes to `output/<prefix>__<year>.parquet`.
- `src/merge_variables.py`: merges all fetched variables into per-year parquet files under `data/.../output/<geo>_yearly/`.

The census variable codes that are used to create the time series are defined in the `yaml` file stored in `conf/variables/<config_yaml>`. The data paths attached to the pipeline are defined in `conf/datapaths/<config_yaml>`.

### Fix the key params in config
For example:
```
  - datapaths: core_cannon
  - variables: core
```

To extract all variables and merge them use the snakemake workflow.

```bash
# Create and activate the conda environment
conda env create -f requirements.yml
conda activate census_series

# Set your Census API key
export CENSUS_API_KEY='your_api_key_here'
export PYTHONPATH='.'
```

### Create the data directory paths
python src/create_datapaths.py

### Execute the Snakemake pipeline
```
snakemake --cores 1 #select number of cores
```

## Run Dockerized Pipeline

For an isolated and reproducible environment, the pipeline is also dockerized. To run the Dockerized task decide in which folder you want the output files to be stored <output_path> and run

```bash
# Run the Dockerized pipeline 
docker pull nsaph/census_series:latest
docker run -v <output_path>:/app/data/output/ --env CENSUS_API_KEY=<your_api_key_here> nsaph/census_series:latest
```

Note: Remember to replace your_api_key_here with your actual Census API key.

If you want to build your own container try

```
# To build the Docker image
docker build -t census_series .
```
For multiplatform
```
docker buildx build --platform linux/amd64,linux/arm64 -t nsaph/census_series:<version> . --push
```
Remember this step is unnecessary as the built image is available under `nsaph/census_series:latest`.

## Run the Interpolation task

```
python src/interpolate_years geo_type=zcta
```
