import requests
import pandas as pd
import numpy as np
import hydra
import utils.validate as validate

def get_data(year, geo_type, dataset, variable_list, api_key):

    #helper dictionary for URL creation
    geography_dict = {'county': 'county:*', 'state': 'state:*', 'zcta': 'zip%20code%20tabulation%20area:*'}

    #extract the required geography for URL creation
    geography = geography_dict[geo_type]

    #structure for api endpoint
    api_endpoint = f'https://api.census.gov/data/{year}/{dataset}'

    # Construct the URL with the parameters
    url = f'{api_endpoint}?get={variable_list}&for={geography}&key={api_key}'
    #print(url)

    # Make the API request
    response = requests.get(url)

    # Process the response
    if response.status_code == 200:
        status = 200
        #save the response in json 
        data = response.json()
        #convert to dataframe 
        df = pd.DataFrame(data[1:], columns=data[0])
        # The data variable now contains the requested data for all counties.
    else:
        status = -1
        df = None

    if status == 200:
        if geo_type == 'county':
            col_list = [geo_type, 'state'] + variable_list.split(',')
            df = df[col_list]
            df['county'] = df['county'] + df['state']
            df.drop(columns=['state'], inplace=True)
            return True, df.set_index('county')
        if geo_type == 'state':
            col_list = ['state'] + variable_list.split(',')
            df = df[col_list]
            return True, df.set_index('state')
        if geo_type == 'zcta':
            col_list = ['zip code tabulation area'] + variable_list.split(',')
            df = df[col_list]
            df.rename(columns={'zip code tabulation area':'zcta'},inplace=True)
            return True, df.set_index('zcta')
    
    else:
        return False, None

def process_variable_dict(year, geo_type, dataset, variable_codes, variable_label, api_key):
    # == identify the variables to fetch ==
    if 'den' in variable_codes: 
        den_list = variable_codes['den']
        num_list = variable_codes['num']
        if den_list is None and num_list is None:
            return None
        all_var_list = den_list + num_list
    
    else:
        num_list = variable_codes['num']
        all_var_list = num_list

    variables = ','.join(all_var_list)

    if variables is None:
        return None

    # == fetch the data ==
    status, df = get_data(year, geo_type, dataset, variables, api_key)

    if status == True:
        # == transform to ratio ==
        df = df.apply(pd.to_numeric, errors='coerce')
        if 'den' in variable_codes:
            df[variable_label] = df[num_list].sum(axis=1) / df[den_list].sum(axis=1)
        else:
            df[variable_label] = df[num_list].sum(axis=1)

        df.drop(columns=all_var_list, inplace=True)

        # == clean df ==
        # Fill missing values with NaN
        df = df.fillna(np.nan)
    
        numerical_columns = df.select_dtypes(include=[np.number]).columns

        # Replace negative values with NaN in numerical columns
        for column in numerical_columns:
            df[column] = df[column].apply(lambda x: np.nan if pd.notna(x) and x < 0 else x)

        # Assign year
        # if dataset contains 'acs5', assign the midyear of the ACS5 5-year estimates
        if 'acs5' in dataset:
            df['year'] = year - 2
        else: 
            df['year'] = year

        # Reset index
        df.reset_index(inplace=True)
        return df

    else:
        return None

@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg):
    validate.validate_census_variable(cfg)
    variable = cfg.variable

    var_df_list = []
    for survey in cfg.census.variables[variable]:
        if cfg.census.variables[variable][survey].segments is None:
            continue
        for segment in cfg.census.variables[variable][survey].segments:
            for year in segment.years:
                dataset = segment['dataset']
                variable_codes = segment['codes']
                variable_label = variable
                geo_type = cfg.census.geo_type

                print(f"Generating for year: {year}, geo_type {geo_type}, dataset {dataset}, variable {variable_label}")
                df = process_variable_dict(year, geo_type, dataset, variable_codes, variable_label, cfg.api_key)
                if df is None:
                    raise ValueError(f"Cannot generate for year: {year}, geo_type {geo_type}, dataset {dataset}, variable {variable_label}")
                else:                            
                    df['survey'] = survey
                    # Set index
                    if geo_type == 'county':
                        df.set_index(['survey','year','county'], inplace=True)
                    if geo_type == 'state':
                        df.set_index(['survey','year','state'], inplace=True)
                    if geo_type == 'zcta':
                        df.set_index(['survey','year','zcta'], inplace=True)
                    var_df_list.append(df)
    var_df = pd.concat(var_df_list)

    # assign a file name based on dataset name and variable
    filename = f'{cfg.census.dataset_name}__{variable}.parquet'
    #var_df.reset_index(inplace=True)
    var_df.to_parquet(f'data/intermediate/census_variables/{filename}')
    print(f"GENERATED file {filename}")

if __name__ == "__main__":
    main()
    