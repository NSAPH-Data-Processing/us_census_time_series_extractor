# US Census Time Series Extractor Pipeline README 

## 1. Dataset description 

This repository [NSAPH Data Processing – us_census_time_series_extractor](https://github.com/NSAPH-Data-Processing/us_census_time_series_extractor)
 extracts longitudinal sociodemographic time series from the US Census Bureau, from Decennial Census (SF1/SF3/DHC), ACS 1-year (ACS1), and ACS 5-year (ACS5) data. It organizes variable definitions in YAML, fetches per-variable files via the Census API, merges variables into per-year datasets, and can optionally align and interpolate results to consistent geographic bases (e.g., ZCTA 2010, ZCTA 2020).

### Download Methodology and Data Access

American Community Survey 5-Year Data (ACS5)
- Time Coverage: Annual; in this pipeline we use 2009–2022 for counties and 2011–2022 for ZCTAs.
- Population: All 50 states including the District of Columbia, Puerto Rico, and other U.S. territories.
- Geographical Coverage: nation, states (including DC and Puerto Rico), metropolitan areas, congressional districts, counties, places, tracts, and block groups.
- ZCTA Coverage: available for ACS5 and used here starting 2011.
- Data Source: ACS provides yearly social, economic, demographic, and housing characteristics.
- API Datasets Used: `acs/acs5`, and `acs/acs5/profile` for percentage/profile tables.

American Community Survey 1-Year Data (ACS1)
- Time Coverage: 2005–2022 for county/state-level geographies.
- Population: All 50 states including DC, Puerto Rico, and other U.S. territories.
- Geographical Coverage: nation, states, DC, Puerto Rico, congressional districts, metropolitan areas, and counties/places with populations ≥ 65,000.
- ZCTA Coverage: not available in ACS1.
- API Dataset Used: `acs/acs1`.

Decennial Census (SF1/SF3/DHC)
- Time Coverage: 2000, 2010, 2020 (variable availability depends on survey).
- Geographical Coverage: SF1 released for each state, DC, Puerto Rico, and the United States; SF3 (2000) includes sample-based socioeconomic characteristics; DHC (2020) provides detailed characteristics.
- Data Source: SF1 covers 100% count topics (sex, age, race, Hispanic origin, households, group quarters). SF3 and DHC extend socioeconomic detail.
- API Datasets Used: `dec/sf1`, `dec/sf3`, `dec/dhc`.

Access and configuration
- Geographies supported: `zcta`, `county`, `state`.
- Variable definitions (names and codes by survey/year) are declared in `conf/variables/*.yaml` (full configs: [conf](https://github.com/NSAPH-Data-Processing/us_census_time_series_extractor/tree/main/conf)).
- `valid_years` governs the years fetched/merged; segments select the correct dataset via `from_year` rules.

### Variable Definitions Schema

Each variable is defined under `names:` with survey-specific segments that specify when the dataset or codes change. Key fields:
- `from_year`: first year the segment applies; subsequent years use this segment until the next segment.
- `dataset`: Census API dataset path (e.g., `dec/sf1`, `dec/dhc`, `acs/acs1`, `acs/acs5`).
- `codes.num`: list of variable codes to sum for the numerator.
- `codes.den` (optional): list of codes to sum for the denominator. If present, the pipeline computes `100 × sum(num) / sum(den)`; otherwise it computes `sum(num)`[src/fetch_variables.py](https://github.com/NSAPH-Data-Processing/us_census_time_series_extractor/blob/main/src/fetch_variables.py).

### Subfolders overview: core vs 65_plus vs asian_not_hispanic

These YAML profiles define different variable bundles and year coverage:

- `core.yaml`
	- Scope: broad sociodemographic set (population, age groups, race categories, Hispanic, education enrolled/attained, poverty, housing units/tenure, median home value, median household income, median age).
	- Surveys/years: includes Decennial (2000/2010/2020 where applicable), ACS1 (2005–2022 for county/state), ACS5 (2009–2022 for county; 2011–2022 for ZCTA).
	- Use for most demographic analyses, population exposure studies, environmental epidemiology, and any work needing standard Census variables across long time spans and geographies.

- `65_plus.yaml`
	- Scope: a targeted subset of variables specifically about people aged 65+: `population`, `pop_over_65_years`, `pop_65_plus_high_school_not_attained`, `pop_65_plus_below_poverty_level`.
	- Surveys/years: ACS5 only; counties (2009–2022), ZCTAs (2011–2022). Decennial not included in this profile.
	- Use when analyses center on 65+ populations.

- `asian_not_hispanic.yaml`
	- Scope: language and ethnicity metrics: `% foreign_born`, `% speak English less than very well`, `% speak Spanish at home`, `% speak Spanish at home and English < very well`, `% speak Asian/Pacific languages at home`, corresponding English proficiency, `% Hispanic`, `% Asian not Hispanic`.
	- Surveys/years: Decennial 2000 where available; ACS5 for 2009–2022 (counties) and 2011–2022 (ZCTAs). Many metrics use ACS profile tables (`acs/acs5/profile`).
	- Use for language-use, immigration, and ethnicity-focused analyses, especially distinguishing Asian not Hispanic groups.

## 2. File Structure and Relationships

### Output Folder Struture 

Below is the outputs folder structure :

```text
social/demographics__census
├─ 65_plus/
│  ├─ county_yearly/
│  │  └─ acs5_<yyyy>.parquet
│  └─ zcta_yearly/
│     └─ acs5_<yyyy>.parquet
│
├─ asian_not_hispanic/
│  ├─ county_yearly/
│  │  └─ {acs5|dec}_<yyyy>.parquet
│  └─ zcta_yearly/
│     └─ {acs5|dec}_<yyyy>.parquet
│
├─ core/
│  ├─ county_yearly/
│  │  └─ {acs1|acs5|dec}_<yyyy>.parquet
│  ├─ zcta_yearly/
│  │  └─ {acs5|dec}_<yyyy>.parquet
│     └─ demographics__census__core__zcta_yearly__<yyyy>.parquet  # interpolated outputs
```
Note: `<yyyy>` is the output year.

### Snakemake Workflow

The pipeline is orchestrated by Snakemake and parameterized by Hydra configs.

Key components:
- `Snakefile`: defines high-level workflow rules.
- `src/create_datapaths.py`: creates local data directories and/or symlinks to shared storage as specified by configs.
- `src/fetch_variables.py`: fetches a single variable across valid years; writes parquet to `data/.../input/`.
- `src/interpolate_years.py`(optional step): aligns to a specified geographic basis (via crosswalks) and linearly interpolates to annual series; writes to `output/<prefix>__<year>.parquet`.
- `src/merge_variables.py`: merges all fetched variables into per-year parquet files under `data/.../output/<geo>_yearly/`.

## 3. Data Dictionary

Core columns present across outputs:
- `survey`: data source;  values `dec`, `acs1`, `acs5`.
- `year`: integer year of the estimate; ACS5 uses period end-year.
- Geography ID: one of `zcta`, or `county`depending on `geo_type`.

Selected variable columns:
- `population`: total population count.
- `median_age`: median age in years.
- `pop_under_20_years`: count of people aged 0–19.
- `pop_35_49_years`, `pop_50_64_years`, `pop_over_65_years`: age-group counts.
- `pop_white`, `pop_black`, `pop_native`, `pop_asian`: race-alone counts.
- `pop_hispanic`: count of people of Hispanic or Latino origin.
- `pop_non_us_citizen`: count of non–U.S. citizens.
- `pop_higher_education_enrolled`: enrolled in undergraduate or graduate/professional school.
- `pop_higher_education_attained`: attained bachelor’s, master’s, professional, or doctoral degree.
- `pop_poverty`: count below poverty level.
- `housing_units`: total housing units.
- `housing_occupied`: occupied housing units.
- `housing_renter_occupied`: renter-occupied units.
- `housing_owner_occupied`: owner-occupied units (mortgage or free and clear).
- `median_home_value`: median value (USD) of owner-occupied housing.
- `median_household_income`: median household income (inflation-adjustment per survey conventions).

Asian/Language profile variables (in `asian_not_hispanic`):
- `pct_foreign_born`: percent foreign-born.
- `pct_speak_english_less_than_very_well`: percent with limited English proficiency.
- `pct_speak_spanish_at_home`: percent speaking Spanish at home.
- `pct_speak_spanish_at_home_english_less_than_very_well`: percent Spanish-at-home with limited English.
- `pct_speak_asian_pacific_at_home`: percent speaking Asian/Pacific languages at home.
- `pct_speak_asian_pacific_at_home_english_less_than_very_well`: percent Asian/Pacific-at-home with limited English.
- `pct_hispanic`: percent Hispanic.
- `pct_asian_not_hispanic`: percent Asian, not Hispanic.

65+ profile variables (in `65_plus`):
- `population`: total population count.
- `pop_over_65_years`: count of people aged 65+.
- `pop_65_plus_high_school_not_attained`: count 65+ without high school diploma.
- `pop_65_plus_below_poverty_level`: count 65+ below poverty level.

## 4. Dataset Motivation

**a. What is the motivation behind the creation of this dataset?**
- To enable reproducible, comparable sociodemographic time series across changing Census surveys and geographies. The pipeline harmonizes variables, applies documented rules for computing them, and optionally aligns geographies to fixed bases to support longitudinal research.

**b. Who funded the creation of this dataset?**

- This work contributes to U24ES035309, CAFE: a Research Coordinating Center to ´
Convene, Accelerate, Foster, and Expand the Climate Change and Health Community of Practice (PI: Wellenius,
Nori-Sarma, Dominici).

**c. What groups/people were involved in the collection/generation/processing of this data?**

- Dataset generated and processed by the data science team at NSAPH (National Study on Air Pollution and Health).

## 5. Dataset Composition

**a. Completeness**

- Coverage varies by survey and geography: ACS1 has no ZCTA; ACS5 ZCTA begins 2011; Decennial available at 2000/2010/2020 depending on variable.
- Variables tied to specific datasets may be unavailable in some years (`dataset: null`), leading to missing values in merged outputs.
- API availability and upstream changes can result in occasional gaps; such cases are surfaced as `NaN` post-cleaning.
- Interpolation fills gaps between observed years to create continuous annual series, but it does not generate data for geographies or years where no source information exists.

**b. Errors, Noise, or Redundancy**

- Negative values from API responses are treated as missing (`NaN`); non-numeric entries are coerced to `NaN`.
- ACS profile percentages are used as reported and may not sum to exactly 100 due to rounding.
- Crosswalk alignment redistributes values by weights; small rounding differences vs. original boundaries are expected.

**c. External Sources and Citations**

While this dataset is self-contained —meaning all files are preprocessed, cleaned, and ready for analysis—it was created using external publicly available datasets, which were processed through a reproducible pipeline.

External sources include:
- US Census API (Decennial: `dec/sf1`, `dec/sf3`, `dec/dhc`; ACS: `acs/acs1`, `acs/acs5`, `acs/acs5/profile`).
- US Census API: https://api.census.gov/data.html
- ACS technical docs: https://www.census.gov/programs-surveys/acs
- Decennial technical docs: https://www.census.gov/programs-surveys/decennial-census/technical-documentation.html

- ZCTA 2000 → 2010 crosswalk used in this pipeline is sourced from IPUMS NHGIS.
-Citation: IPUMS NHGIS. Zip Code Tabulation Area (ZCTA) 2000 to 2010 Geographic Crosswalk. Minnesota Population Center, University of Minnesota. https://www.nhgis.org/ (see Geographic Crosswalks documentation).

**d. Data De-sensitized**

- No personally identifiable information is included.
- Data are aggregates at public statistical geographies (ZCTA, county, state).
- No small-area suppression is applied by this pipeline; users should assess disclosure risks only if joining with sensitive data.

## 6. Collection and Analysis

**Software and Tools** 

From `environment.yml` (channels: conda-forge, defaults):
- Python 3.11: runtime for all scripts and notebooks.
- pandas: tabular data processing, type coercion, joins, reshaping.
- pyarrow: parquet read/write and efficient columnar memory format.
- duckdb: fast in-process SQL; used to slice and export per-year parquet files.
- hydra-core: configuration composition from `conf/` (datapaths, variables, interp).
- snakemake: workflow orchestration for fetching and merging steps.
- census: US Census API Python client (optional helper alongside direct API calls).
- censusdis: high-level Census data access utilities, useful in notebooks/analysis.
- ipykernel: Jupyter kernel support for `.ipynb` exploration in `notes/`.

**Reproducibility**  

- Clone the repository and create a conda environment :

```zsh
conda env create -f environment.yml
conda activate census_series
export PYTHONPATH=.
export CENSUS_API_KEY='<your_api_key>'
```
Set `CENSUS_API_KEY` (free key from the Census Bureau).

Create data paths (local dirs and/or symlinks):
```zsh
python src/create_datapaths.py
```

Run the full Snakemake workflow (fetch all variables and merge):
```zsh
snakemake --cores 1
```

Run a single variable fetch manually (useful for debugging):
```zsh
python src/fetch_variables.py geo_type=county survey=acs1 variable=pop_native
```

Run merging manually:
```zsh
python src/merge_variables.py
```

Run interpolation/alignment (optional, driven by `conf/interp.yaml`):
```zsh
python src/interpolate_years.py
```

Docker (optional): a `Dockerfile` is provided. You can build and run locally if you prefer isolated execution.

All scripts, configuration files, and the environment definition can be found in the GitHub repository:  
🔗 [NSAPH Data Processing – us_census_time_series_extractor](https://github.com/NSAPH-Data-Processing/us_census_time_series_extractor)

## 7. Dataset Composition and Processing

**a. What preprocessing, labeling, or cleaning was done to the dataset to develop the final product?** 

<p>The dataset is preprocessed to ensure consistency across years and geographies. Census variables are downloaded, cleaned (with invalid values converted to missing), and computed as counts or percentages according to configuration. Each variable is stored separately, then aligned to a common geographic basis using published crosswalks when boundaries change (if needed). Linear interpolation provides intermediate annual estimates without extrapolation. Finally, variables are merged into per-year, per-geography parquet files. The resulting outputs use standardized variable names ready for analysis in R or Python.</p>

- `src/create_datapaths.py`: materializes directories/symlinks from `conf/datapaths/*`; ensures `data/<profile>/{input,output,xwalk}` exist.
- `src/fetch_variables.py`: selects dataset segments by `from_year`, fetches for `valid_years`, coerces to numeric, computes counts/percents, labels (`year`,`survey`), writes per-variable parquet under `data/<profile>/input/...`.
- `src/interpolate_years.py` (optional): composes sequences per `conf/interp/*:intervals`, applies crosswalks where `align` is defined, performs linear interpolation, generates `data/<profile>/output/<prefix>__<year>.parquet`.
- `src/merge_variables.py`: loads per-variable parquet for a `geo_type`+`survey`, aligns to `['year','survey',<geo>]`, merges columns, writes one parquet per year via DuckDB to `data/<profile>/output/<geo>_yearly/...`.

**b. Is the source data included in this dataset or otherwise preserved and accessible?**

- The original raw source files are not included in this dataset. However, all source data used to generate this dataset are fully accessible via the links included in the External Sources and Citations section.



