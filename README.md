# Census 

- [Introduction](#introduction)
- [Data Description](#data-description)
- [Codebook](#codebook)
- [Repository Content](#repository-content)
- [Data Lineage](#data-lineage)
- [Processing Rules](#processing-rules)
- [Run](#run)

## Introduction
The project streamlines the extraction and analysis of demographic data from American Community Survey 5-Year Data (ACS5), American Community Survey 1-Year Data (ACS5) and Decennial Census (SF1).

## Data Description

### American Community Survey 5-Year Data (ACS5)

- Time Coverage : 2007 - 2018
- Population: All 50 states including the District of Columbia, Puerto Rico, and other U.S. territories.
- Geographical Coverage: nation, all states (including DC and Puerto Rico), all metropolitan areas, all congressional districts (116th congress), all counties, all places, all tracts and block groups.
- ZCTA Coverage: 33120
- Data Source: The American Community Survey (ACS) is an ongoing survey that provides data every year -- giving communities the current information they need to plan investments and services. The ACS covers a broad range of topics about social, economic, demographic, and housing characteristics of the U.S. population.

### American Community Survey 1-Year Data (ACS5)

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

## Codebook

### For ACS 1-year and ACS 5-year estimates

| Variable Name | Description | Derivation |
|---|---| --- |
| pct_blk  | % of the population listed as black  | ```B02001_003E/B02001_001E``` <br> B02001_003E: Estimate!!Total!!Black or African American alone <br> B02001_001E: Estimate!!Total - Race |
| medhouseholdincome | median household income | `B19013_001E`  <br> B19013_001E: : Median Household Income In The Past 12 Months In 2011 Inflation-Adjusted Dollars |
| pct_owner_occ | % of housing units occupied by their owner  | `For Years 2009 - 2014: (B11012_004E + B11012_008E + B11012_011E + B11012_014E)/ B11012_001E` <br> B11012_004E: Estimate!!Total!!Family households!!Married-couple family!!Owner-occupied housing units <br> B11012_008E: Estimate!!Total!!Family households!!Other family!!Male householder, no wife present!!Owner-occupied housing units <br> B11012_011E: Estimate!!Total!!Family households!!Other family!!Female householder, no husband present!!Owner-occupied housing units B11012_014E: Estimate!!Total!!Nonfamily households!!Owner-occupied housing units <br> B11012_001E: Estimate!!Total - HOUSEHOLD TYPE BY TENURE <br> `For Years 2015 - 2018: B25011_002E/B25011_001E` <br> B25011_002E: Estimate!!Total!!Owner occupied <br> B25011_001E: Estimate!!Total: TENURE BY HOUSEHOLD TYPE (INCLUDING LIVING ALONE) AND AGE OF HOUSEHOLDER|
| hispanic| % of the population identified as Hispanic, regardless of reported race  | `B03003_003E/B03003_001E` <br> B03003_003E: Estimate!!Total!!Hispanic or Latino <br> B03003_001E: Estimate!!Total |
| education | % of the population older than 65 not graduating from high school  | `(B15001_036E+B15001_037E+B15001_077E+B15001_078E)/(B15001_035E+B15001_076E)` <br> B15001_036E: Estimate!!Total!!Male!!65 years and over!!Less than 9th grade <br>  B15001_037E: Estimate!!Total!!Male!!65 years and over!!9th to 12th grade, no diploma <br> B15001_077E: Estimate!!Total!!Female!!65 years and over!!Less than 9th grade <br> B15001_078E: Estimate!!Total!!Female!!65 years and over!!9th to 12th grade, no diploma <br> B15001_035E: Estimate!!Total!!Male!!65 years and over <br> B15001_076E: Estimate!!Total!!Female!!65 years and over |


### For Decennial SF1

| Variable Name | Description | Derivation |
|---|---| --- |
| pct_blk  | % of the population listed as black  | ``` For the year 2010: P006003/P006001``` <br> P006003: Total races tallied!!Black or African American alone or in combination with one or more other races <br> P006001: Total races tallied <br> ``` For the year 2000: P007003/P007001``` <br> P007003: Estimate!!Total!!Black or African American alone <br> P007001: Estimate!!Total - Race  |
| pct_owner_occ   |% of housing units occupied by their owner   | ``` For the year 2010: (H004002 + H004003) /H004001``` <br> H004002 : Total!!Owned with a mortgage or a loan <br> H004003: Total!!Owned free and clear <br> H004001: Total - Tenure <br>``` For the year 2000: H004002/H004001``` <br> H004002: Total!!Owner occupied <br> H004001: Total  |
| hispanic  | % of the population identified as Hispanic, regardless of reported race  | ``` For the year 2010: P004002/P004001``` <br> P004003: Total!!Hispanic or Latino <br> P004001: Total <br> ``` For the year 2000: P004002/P001001``` <br> P004002: Total!!Hispanic or Latino <br> P001001: Total Population  |

## Repository Content

The repository contains: 

- [data/input](https://github.com/NSAPH-Data-Processing/census/tree/main/data/input): The directory for input yaml files for each dataset ACS 1-year, ACS 5-year and Decennial SF1 estimates. 
- [census_fetch.py](https://github.com/NSAPH-Data-Processing/census/blob/main/census_fetch.py): The main script for querying Census API and generating final datasets.
- [requirements.yml](https://github.com/NSAPH-Data-Processing/census_acs5/blob/dev/requirements.yml): Environment setup file for result reproducibility.

## Data Lineage

- **Data Source** :The primary data source for this project is the [American Community Survey 5-Year Data (ACS5)](https://www.census.gov/programs-surveys/acs/about.html), which is publicly available and maintained by U.S. Census Bureau. 

- **Extraction** : We leverage the Census API to efficiently extract data.

- **Processing & Final Dataset** : We transform the subset of variables obtained from the API and generate the final datasets for each respective year.

## Processing Rules

**Processing rules applied in census_fetch.py**

To align with the aggregated nature of ACS estimates over 5-year periods, a specific processing rule is employed within the project. Each dataset generated from ACS data is internally tagged to a year that is 2 years prior. This tagging ensures that the data extracted in a given year corresponds to the ACS data collected 2 years later, providing consistency with the 5-year estimates.

For instance, when extracting data for the year 2020 from the ACS, the data is tagged internally as ACS 2018. This alignment respects the fact that the 2020 5-year estimates encompass ACS data collected from January 1, 2016, through December 31, 2020. This approach enables accurate and meaningful analysis while considering the temporal aggregation inherent in ACS data reporting.

**American Community Survey 1-Year Data and Hispanic Variable**

Hispanic data was incorporated starting from the 2009 ACS 1-year estimates and hence not available for the years 20005-2008 for ACS 1-Year estimates and marked as NULL in the data.


## Run 

You can run the pipeline steps manually or run the snakemake pipeline described in the Snakefile.

**run pipeline steps manually**

```bash
conda env create -f requirements.yml
conda activate census_acs5_env
export CENSUS_API_KEY='your_api_key_here'
python src/census_fetch.py --var_yaml census_acs5.yaml --geo_type county --census_type acs --table_name acs5
```

**run snakemake pipeline**
or run the pipeline:

```bash
conda env create -f requirements.yml
conda activate census_acs5_env
export CENSUS_API_KEY='your_api_key_here'
snakemake --cores 4
```