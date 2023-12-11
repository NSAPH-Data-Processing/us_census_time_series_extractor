#import necessary libraries
import argparse
import requests
import pandas as pd
import numpy as np
import yaml
import os


def get_data(year, geo_type, table_name, variable_list, census_type):

    #helper dictionary for URL creation
    geography_dict = {'county': 'county:*', 'state': 'state:*', 'zcta': 'zip%20code%20tabulation%20area:*'}

    #extract the required geography for URL creation
    geography = geography_dict[geo_type]

    #structure for api endpoint
    api_endpoint = f'https://api.census.gov/data/{year}/{census_type}/{table_name}'

    # Construct the URL with the parameters
    url = f'{api_endpoint}?get={variable_list}&for={geography}&key={args.api_key}'
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
            col_list = ['state']+ variable_list.split(',')
            df = df[col_list]

            df.set_index('state', inplace=True)

        if geo_type == 'zcta':
            col_list = ['zip code tabulation area'] + variable_list.split(',')
            df = df[col_list]
            df.rename(columns={'zip code tabulation area':'zcta'},inplace=True)
            df.set_index('zcta', inplace=True)

        return True,df
    
    else:
        return False, None


def process_variable_dict(year, geo_type, census_type, table_name, year_variables, variable_name ):

    if 'den' in year_variables: 
        den_list = year_variables['den']
        num_list = year_variables['num']
        if den_list is None and num_list is None:
            return None
        all_var_list = den_list + num_list
    
    else:
        num_list = year_variables['num']
        all_var_list = num_list

    variables = ','.join(all_var_list)

    if variables is None:
        return None

    status, df = get_data(year, geo_type, table_name, variables, census_type)

    if status == True:
        df = df.apply(pd.to_numeric, errors='coerce')
        if 'den' in year_variables:
            df[variable_name] = df[num_list].sum(axis=1) / df[den_list].sum(axis=1)
        else:
            df[variable_name] = df[num_list].sum(axis=1)

        df['year'] = year
        df.drop(columns=all_var_list, inplace=True)

        # Fill missing values with NaN
        df = df.fillna(np.nan)
    
        numerical_columns = df.select_dtypes(include=[np.number]).columns

        # Replace negative values with NaN in numerical columns
        for column in numerical_columns:
            df[column] = df[column].apply(lambda x: np.nan if pd.notna(x) and x < 0 else x)

        return df.reset_index()
    
    else:
        return None

if __name__ == "__main__":

    # Set up command-line argument parser       
    parser = argparse.ArgumentParser(description='Process Census data.')

    # Define command-line arguments   
    parser.add_argument('--var_yaml', type=str, help='name of the yaml file') 
    parser.add_argument('--geo_type', type=str, choices=['county', 'state', 'zcta'], help='Geography type')
    parser.add_argument('--census_type', type=str, help='Type of Census data')
    parser.add_argument('--table_name', type=str, help='Name of the table')
    parser.add_argument('--api_key', type=str, default=os.environ['CENSUS_API_KEY'])

    # Parse command-line arguments
    args = parser.parse_args()

    # Extract values from command-line arguments
    geo_type = args.geo_type
    census_type = args.census_type
    table_name = args.table_name
    yaml_file = args.var_yaml
    api_key = args.api_key


    data_dir_path = './data/input'
    yaml_file_path = os.path.join(data_dir_path, yaml_file)

    with open(yaml_file_path, 'r') as file:
        census_doc = yaml.safe_load(file)

    variables_list = census_doc.keys()

    df_list = []

    if geo_type == 'county':
        id_variables = ['county', 'state', 'year']
    elif geo_type == 'zcta':
        id_variables = ['zcta', 'year']
    else:
        id_variables = ['state', 'year']

    for variable in variables_list:
        for year in census_doc[variable]:
            variable_year_doc = census_doc[variable][year]
            df = process_variable_dict(year, geo_type, census_type, table_name, variable_year_doc, variable)
            if df is not None:
                melted_df = pd.melt(df, id_vars=id_variables, value_vars=[variable], var_name='variable', value_name='value')
                df_list.append(melted_df)
            else: 
                print(f"'WARN: Cannot generate for year: {year}, variable {variable}")
    
    #concat the df
    final_df = pd.concat(df_list, axis=0, ignore_index=True)
    final_df['year'] = final_df['year'].astype('int')

    if table_name == 'acs5':
        final_df['year'] = final_df['year'] - 2 

    # Generate a file name based on variable, table, year, and geography type
    file_name = f'{table_name}_{geo_type}' + '.csv'

    # Save the DataFrame to a CSV file
    file_save_dir = './data/output'
    file_save_path = os.path.join(file_save_dir, file_name)
    final_df.to_csv(file_save_path)
    print(f"GENERATED file = '{table_name}_{geo_type}.csv'")
