# US Census Time Series README 

## 1. Dataset description 

This dataset can be fully re-generated running the pipeline that is shared in the repository [NSAPH Data Processing – us_census_time_series_extractor](https://github.com/NSAPH-Data-Processing/us_census_time_series_extractor)
The pipeline extracts longitudinal sociodemographic time series from the US Census Bureau, from Decennial Census (SF1/SF3/DHC), ACS 1-year (ACS1), and ACS 5-year (ACS5) data. It organizes variable definitions in YAML, fetches per-variable files via the Census API, merges variables into per-year datasets, and can optionally align and interpolate results to consistent geographic bases (e.g., ZCTA 2010, ZCTA 2020).

## 2. File Structure and Relationships

### Output Folder Struture 

Below is the outputs folder structure :

```text

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

### Subfolders overview: core vs 65_plus vs asian_not_hispanic


- `core`
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

## 3. Data Dictionary

Core columns have outputs present across:
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

## 7. Dataset Composition and Processing



**Is the source data included in this dataset or otherwise preserved and accessible?**

- The original raw source files are not included in this dataset. However, all source data used to generate this dataset are fully accessible via the links included in the External Sources and Citations section.



