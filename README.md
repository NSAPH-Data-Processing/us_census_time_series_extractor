[![](<https://img.shields.io/badge/Dataverse-10.7910/DVN/SYNPBS-orange>)](https://doi.org/10.7910/DVN/N3IEXS)

# US Census Bureau Time Series Extractor

- [Introduction](#introduction)
- [Data Description](#data-description)
- [Data Dictionary](#data-dictionary)
- [Repository Content](#repository-content)
- [Data Lineage](#data-lineage)
- [Processing Rules](#processing-rules)
- [Run](#run)

## Introduction
This repository streamlines the extraction of time series from American Community Survey 5-Year Data (ACS5), American Community Survey 1-Year Data (ACS1) and Decennial Census (SF1).

## Data Description

### American Community Survey 5-Year Data (ACS5)

- Time Coverage : 2007 - 2018
- Population: All 50 states including the District of Columbia, Puerto Rico, and other U.S. territories.
- Geographical Coverage: nation, all states (including DC and Puerto Rico), all metropolitan areas, all congressional districts (116th congress), all counties, all places, all tracts and block groups.
- ZCTA Coverage: 33120
- Data Source: The American Community Survey (ACS) is an ongoing survey that provides data every year -- giving communities the current information they need to plan investments and services. The ACS covers a broad range of topics about social, economic, demographic, and housing characteristics of the U.S. population.

### American Community Survey 1-Year Data (ACS1)

- Time Coverage : 2005 - 2020
- Population: All 50 states including the District of Columbia, Puerto Rico, and other U.S. territories.
- Geographical Coverage: available for the nation, all 50 states, the District of Columbia, Puerto Rico, every congressional district, every metropolitan area, and all counties and places with populations of 65,000 or more.
- ZCTA Coverage: No ZCTA coverage
- Data Source: The American Community Survey (ACS) is an ongoing survey that provides data every year -- giving communities the current information they need to plan investments and services. The ACS covers a broad range of topics about social, economic, demographic, and housing characteristics of the U.S. population.

### Decennial Census

- Time Coverage: For the years 2000, 2010
- Geographical Coverage: Summary File 1 (SF 1) is released as individual files for each of the 50 states, the District of Columbia, and
Puerto Rico, and for the United States.
- Data Source: Summary File 1 (SF 1) contains the data compiled from the questions asked of all people and about every housing unit. Population items include sex, age, race, Hispanic or Latino origin, household relationship, household type, household size, family type, family size, and group quarters. 

## Data Dictionary

| Column Name| Description|
|---------------------------------|------------------------------------------------------------------------|
| `survey`| Type of survey, it takes one of the following values: dec, acs1, acs5|
| `year`| Year of the variable estimates.|
| geographic level| Id of geogragraphies at a given geographic level. The column name takes the name of the geographic level (zcta, county, state)|
| Various sociodemographic columns| Columns containing variables related to sociodemographic characteristics such as population distribution by age groups, ethnic composition, housing statistics, and other demographic and socioeconomic variables. The column name is the name of the variable|

## Repository Content

The repository contains: 

- [conf/](conf/): configuration files. 
- [src/fetch_variables.py](src/fetch_variables.py): the main script for querying Census API.
- [requirements.yml](requirements.yml): conda environment setup.

## Data Lineage

- **Data Source** :The primary data source for this project is the [American Community Survey 5-Year Data (ACS5)](https://www.census.gov/programs-surveys/acs/about.html), which is publicly available and maintained by U.S. Census Bureau. 

- **Extraction** : We leverage the Census API to efficiently extract data.

- **Processing & Final Dataset** : We transform the subset of variables obtained from the API and generate datasets of selected sociodemographic concepts.

## Processing Rules

**Processing rules**

To align with the aggregated nature of ACS estimates over 5-year periods, a specific processing rule is employed within the project. Each dataset generated from ACS data is internally tagged to a year that is 2 years prior. This tagging ensures that the data extracted in a given year corresponds to the ACS data collected 2 years later, providing consistency with the 5-year estimates.

For instance, when extracting data for the year 2020 from the ACS, the data is tagged internally as ACS 2018. This alignment respects the fact that the 2020 5-year estimates encompass ACS data collected from January 1, 2016, through December 31, 2020. This approach enables accurate and meaningful analysis while considering the temporal aggregation inherent in ACS data reporting.

**American Community Survey 1-Year Data and Hispanic Variable**

Hispanic data was incorporated starting from the 2009 ACS 1-year estimates and hence not available for the years 20005-2008 for ACS 1-Year estimates.


## Run 

### Pipeline

You can run the pipeline steps manually or run the snakemake pipeline described in the Snakefile.

**Run the pipeline steps manually to fetch a single variable**

The census variable codes that are used to create the time series are defined in the `yaml` file stored in `conf/variables/<config_yaml>`. The data paths attached to the pipeline are defined in `conf/datapaths/<config_yaml>`.

# Fix the key params in config
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

**Run snakemake pipeline**

The census variable codes that are used to create the time series are defined in the `yaml` file stored in `conf/variables/<config_yaml>`. The data paths attached to the pipeline are defined in `conf/datapaths/<config_yaml>`.

# Fix the key params in config
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

# Create the data directory paths
python src/create_datapaths.py

# Execute the Snakemake pipeline
snakemake --cores 1 #select number of cores
```

### Dockerized Pipeline

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
