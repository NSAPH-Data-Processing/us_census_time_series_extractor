import requests
import pandas as pd
import numpy as np
import hydra

def get_data(year, geo_type, table_name, variable_list, census_type, api_key):

    #helper dictionary for URL creation
    geography_dict = {'county': 'county:*', 'state': 'state:*', 'zcta': 'zip%20code%20tabulation%20area:*'}

    #extract the required geography for URL creation
    geography = geography_dict[geo_type]

    #structure for api endpoint
    api_endpoint = f'https://api.census.gov/data/{year}/{census_type}/{table_name}'

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
            df.set_index([geo_type,'state'], inplace=True)

        if geo_type == 'state':
            col_list = ['state'] + variable_list.split(',')
            df = df[col_list]

            df.set_index('state', inplace=True)

        if geo_type == 'zcta':
            col_list = ['zip code tabulation area'] + variable_list.split(',')
            df = df[col_list]
            df.rename(columns={'zip code tabulation area':'zcta'},inplace=True)
            df.set_index('zcta', inplace=True)

        return True, df
    
    else:
        return False, None

def process_variable_dict(year, geo_type, census_type, table_name, year_codes, variable_name, api_key):

    if 'den' in year_codes: 
        den_list = year_codes['den']
        num_list = year_codes['num']
        if den_list is None and num_list is None:
            return None
        all_var_list = den_list + num_list
    
    else:
        num_list = year_codes['num']
        all_var_list = num_list

    variables = ','.join(all_var_list)

    if variables is None:
        return None

    status, df = get_data(year, geo_type, table_name, variables, census_type, api_key)

    if status == True:
        df = df.apply(pd.to_numeric, errors='coerce')
        if 'den' in year_codes:
            df[variable_name] = df[num_list].sum(axis=1) / df[den_list].sum(axis=1)
        else:
            df[variable_name] = df[num_list].sum(axis=1)

        df.drop(columns=all_var_list, inplace=True)

        # Fill missing values with NaN
        df = df.fillna(np.nan)
    
        numerical_columns = df.select_dtypes(include=[np.number]).columns

        # Replace negative values with NaN in numerical columns
        for column in numerical_columns:
            df[column] = df[column].apply(lambda x: np.nan if pd.notna(x) and x < 0 else x)

        df['year'] = year
        return df.reset_index()
    
    else:
        return None

@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg):
    # Extract values from command-line arguments
    geo_type = cfg.geo_type
    census_type = cfg.census.census_type
    table_name = cfg.census.table_name
    api_key = cfg.api_key
    
    df_list = []

    for variable, years in cfg.census.codes.items():
        for year, year_codes in years.items():
            df = process_variable_dict(year, geo_type, census_type, table_name, year_codes, variable, api_key)
            if df is not None:
                if geo_type == 'county':
                    df['county'] = df['county'] + df['state']
                    df.drop(columns=['state'], inplace=True)
                melted_df = pd.melt(df, id_vars=[geo_type, 'year'], value_vars=[variable], var_name='variable', value_name='value')
                df_list.append(melted_df)
            else: 
                print(f"'WARN: Cannot generate for year: {year}, variable {variable}, table {table_name}, geo_type {geo_type}'")
    
    #concat the df
    final_df = pd.concat(df_list, axis=0, ignore_index=True)
    final_df['year'] = final_df['year'].astype('int')

    if table_name == 'acs5':
        final_df['year'] = final_df['year'] - 2 # we assign the middle year of the 5-year period

    # Generate a file name based on variable, table, year, and geography type
    # set index
    final_df.set_index([geo_type], inplace=True)
    final_df.to_parquet(f'data/output/census_series/{table_name}_{geo_type}.parquet')
    print(f"GENERATED file = '{table_name}_{geo_type}.parquet'")

if __name__ == "__main__":
    main()
    