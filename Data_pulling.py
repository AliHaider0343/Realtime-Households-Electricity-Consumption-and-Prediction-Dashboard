from datetime import datetime

import pandas as pd
import numpy as np

def generate_random_data_for_over_consumption(start_date, end_date, historical_data):
    # Convert 'Date' column to datetime format
    historical_data['Date'] = pd.to_datetime(historical_data['Date'])
    # Create a date range from start_date to end_date
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    # Initialize lists to store generated data
    month = []
    year = []
    daylight_consumption = []
    night_consumption = []
    daylight_price = []
    night_price = []
    total_consumption = []
    total_price = []
    dates=[]

    # Iterate over each date in the date range
    for date in date_range:
        # If historical data is available for the given month and year
        # Get minimum and maximum values for random generation
        min_daylight_consumption = historical_data['Daylight Consumption in kWh'].min()
        max_daylight_consumption = historical_data['Daylight Consumption in kWh'].max()
        min_night_consumption = historical_data['Night Consumption in kWh'].min()
        max_night_consumption = historical_data['Night Consumption in kWh'].max()

        date_formatted = date.strftime('%Y-%m-%d %H:%M:%S')  # Format date as 'YYYY-MM-DD HH:MM:SS'
        # Generate random values within the historical range
        random_daylight_consumption = np.random.uniform(min_daylight_consumption, max_daylight_consumption)
        random_night_consumption = np.random.uniform(min_night_consumption, max_night_consumption)
        random_daylight_price = random_daylight_consumption*2.64
        random_night_price = random_night_consumption*1.32

        # Calculate total consumption and total price
        total_con = random_daylight_consumption + random_night_consumption
        total_pri = random_daylight_price + random_night_price

        # Append generated data to lists
        month.append(date.month)
        dates.append(date_formatted)
        year.append(date.year)
        daylight_consumption.append(random_daylight_consumption)
        night_consumption.append(random_night_consumption)
        daylight_price.append(random_daylight_price)
        night_price.append(random_night_price)
        total_consumption.append(total_con)
        total_price.append(total_pri)

    # Create a DataFrame from the generated data
    generated_data = pd.DataFrame({
        'Month': month,
        'Year': year,
        'Date': dates,
        'Daylight Consumption in kWh': daylight_consumption,
        'Night Consumption in kWh': night_consumption,
        'Daylight Price in UAH': daylight_price,
        'Night Price in UAH': night_price,
        'Total Consumption': total_consumption,
        'Total Price': total_price
    })

    return generated_data

def update_consumption_data(file_Path):
    data = pd.read_excel(file_Path)
    end_date = datetime.now()
    start_date = max(data['Date'])
    # Extracting only the date part (year, month, day) from the datetime objects
    start_date_date = start_date.date()
    end_date_date = end_date.date()

    # Comparing dates
    if start_date_date != end_date_date:
        generated_data = generate_random_data_for_over_consumption(start_date, end_date, data)
        overall_consumption_data = pd.concat([data, generated_data], ignore_index=True)
        overall_consumption_data.to_excel(file_Path)

def add_random_consumption(file_Path,max_range=4):
    data = pd.read_excel(file_Path)
    data['Date'] = pd.to_datetime(data['Date'])
    # Sort DataFrame by 'Date' column in descending order
    df_sorted = data.sort_values(by='Date', ascending=False)
    latest_row_index = df_sorted.index[0]
    df_sorted.at[latest_row_index, 'Daylight Consumption in kWh'] += np.random.randint(df_sorted.at[latest_row_index, 'Daylight Consumption in kWh'], df_sorted.at[latest_row_index, 'Daylight Consumption in kWh']+max_range)
    df_sorted.at[latest_row_index, 'Night Consumption in kWh'] += np.random.randint(df_sorted.at[latest_row_index, 'Night Consumption in kWh'], df_sorted.at[latest_row_index, 'Night Consumption in kWh']+max_range)
    df_sorted.at[latest_row_index, 'Daylight Price in UAH'] = float(df_sorted.at[latest_row_index, 'Daylight Consumption in kWh'])*2.64
    df_sorted.at[latest_row_index, 'Night Price in UAH'] = float(df_sorted.at[latest_row_index, 'Night Consumption in kWh'])*1.32
    df_sorted.at[latest_row_index, 'Total Consumption'] = df_sorted.at[latest_row_index, 'Night Consumption in kWh']+ df_sorted.at[latest_row_index, 'Daylight Consumption in kWh']
    df_sorted.at[latest_row_index, 'Total Price'] =df_sorted.at[latest_row_index, 'Daylight Price in UAH']+df_sorted.at[latest_row_index, 'Night Price in UAH']
    df_sorted['Date'] = pd.to_datetime(df_sorted['Date'])
    df_sorted.to_excel(file_Path,index=False)


def generate_random_data_for_households(start_date, end_date, historical_data):
    # Convert 'Date' column to datetime format
    historical_data['Date'] = pd.to_datetime(historical_data['Date'])
    # Create a date range from start_date to end_date
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    # Initialize lists to store generated data

    Ovens_and_stoves = []
    Heating_Air_conditioning = []
    Dough_mixers = []
    Ventilation = []
    Refrigeration = []
    Other = []
    total=[]
    dates=[]

    # Iterate over each date in the date range
    for date in date_range:
        min_Ovens_and_stoves = historical_data['Ovens and stoves'].min()
        max_Ovens_and_stoves = historical_data['Ovens and stoves'].max()

        min_Heating_Air_conditioning= historical_data['Heating Air conditioning'].min()
        max_Heating_Air_conditioning = historical_data['Heating Air conditioning'].max()

        min_Dough_mixers = historical_data['Dough mixers'].min()
        max_Dough_mixers = historical_data['Dough mixers'].max()

        min_Ventilation = historical_data['Ventilation'].min()
        max_Ventilation = historical_data['Ventilation'].max()

        min_Refrigeration = historical_data['Refrigeration'].min()
        max_Refrigeration = historical_data['Refrigeration'].max()

        min_Other = historical_data['Other'].min()
        max_Other = historical_data['Other'].max()

        date_formatted = date.strftime('%Y-%m-%d %H:%M:%S')  # Format date as 'YYYY-MM-DD HH:MM:SS'
        # Generate random values within the historical range
        random_Ovens_and_stoves = np.random.uniform(min_Ovens_and_stoves, max_Ovens_and_stoves)
        random_Heating_Air_conditioning = np.random.uniform(min_Heating_Air_conditioning, max_Heating_Air_conditioning)

        random_Refrigeration = np.random.uniform(min_Refrigeration, max_Refrigeration)
        random_Ventilation = np.random.uniform(min_Ventilation, max_Ventilation)

        random_Other = np.random.uniform(min_Other, max_Other)
        random_Dough_mixers = np.random.uniform(min_Dough_mixers, max_Dough_mixers)


        # Calculate total consumption and total price
        total_con = random_Ovens_and_stoves + random_Heating_Air_conditioning + random_Ventilation+random_Refrigeration+random_Other+random_Dough_mixers

        # Append generated data to lists
        dates.append(date_formatted)
        Ovens_and_stoves.append(random_Ovens_and_stoves)
        Heating_Air_conditioning.append(random_Heating_Air_conditioning)
        Dough_mixers.append(random_Dough_mixers)
        Ventilation.append(random_Ventilation)
        Refrigeration.append(random_Refrigeration)
        Other.append(random_Other)
        total.append(total_con)

    # Create a DataFrame from the generated data
    generated_data = pd.DataFrame({
        'Date': dates,
        'Ovens and stoves': Ovens_and_stoves,
        'Heating Air conditioning': Heating_Air_conditioning,
        'Dough mixers': Dough_mixers,
        'Ventilation': Ventilation,
        'Refrigeration': Refrigeration,
        'Other': Other,
        'total': total
    })


    return generated_data

def update_households_data(file_Path):
    data = pd.read_excel(file_Path)
    end_date = datetime.now()
    start_date = max(data['Date'])
    # Extracting only the date part (year, month, day) from the datetime objects
    start_date_date = start_date.date()
    end_date_date = end_date.date()

    # Comparing dates
    if start_date_date != end_date_date:
        generated_data = generate_random_data_for_households(start_date, end_date, data)
        overall_consumption_data = pd.concat([data, generated_data], ignore_index=True)
        overall_consumption_data.to_excel(file_Path)

def add_households_consumption(file_Path,max_range=4):
    data = pd.read_excel(file_Path)
    data['Date'] = pd.to_datetime(data['Date'])
    # Sort DataFrame by 'Date' column in descending order
    df_sorted = data.sort_values(by='Date', ascending=False)
    latest_row_index = df_sorted.index[0]
    columns_to_convert = ['Ovens and stoves', 'Heating Air conditioning', 'Dough mixers', 'Ventilation',
                          'Refrigeration', 'Other']
    df_sorted[columns_to_convert] = df_sorted[columns_to_convert].astype(float)

    df_sorted.at[latest_row_index, 'Ovens and stoves'] += np.random.randint(df_sorted.at[latest_row_index, 'Ovens and stoves'], df_sorted.at[latest_row_index, 'Ovens and stoves']+max_range)
    df_sorted.at[latest_row_index, 'Heating Air conditioning'] += np.random.randint(df_sorted.at[latest_row_index, 'Heating Air conditioning'], df_sorted.at[latest_row_index, 'Heating Air conditioning']+max_range)
    df_sorted.at[latest_row_index, 'Dough mixers'] += np.random.randint(df_sorted.at[latest_row_index, 'Dough mixers'], df_sorted.at[latest_row_index, 'Dough mixers']+max_range)
    df_sorted.at[latest_row_index, 'Ventilation'] += np.random.randint(df_sorted.at[latest_row_index, 'Ventilation'], df_sorted.at[latest_row_index, 'Ventilation']+max_range)
    df_sorted.at[latest_row_index, 'Refrigeration'] += np.random.randint(df_sorted.at[latest_row_index, 'Refrigeration'], df_sorted.at[latest_row_index, 'Refrigeration']+max_range)
    df_sorted.at[latest_row_index, 'Other'] += np.random.randint(df_sorted.at[latest_row_index, 'Other'], df_sorted.at[latest_row_index, 'Other']+max_range)
    df_sorted.at[latest_row_index, 'total'] =df_sorted.at[latest_row_index, 'Ovens and stoves']+df_sorted.at[latest_row_index, 'Heating Air conditioning']+    df_sorted.at[latest_row_index, 'Dough mixers']+df_sorted.at[latest_row_index, 'Ventilation']+df_sorted.at[latest_row_index, 'Refrigeration']+df_sorted.at[latest_row_index, 'Other']

    df_sorted['Date'] = pd.to_datetime(df_sorted['Date'])
    df_sorted.to_excel(file_Path,index=False)


def generate_random_data_for_Solar(start_date, end_date, historical_data):
    # Convert 'Date' column to datetime format
    historical_data['Date'] = pd.to_datetime(historical_data['Date'])
    # Create a date range from start_date to end_date
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    # Initialize lists to store generated data

    Solar_Gird_Generation	 = []
    Consumption_and_Decipation	 = []
    Solar_Saving_and_Battry_backup = []
    dates = []

    # Iterate over each date in the date range
    for date in date_range:
        min_Solar_Gird_Generation = historical_data['Solar Gird Generation'].min()
        max_Solar_Gird_Generation = historical_data['Solar Gird Generation'].max()

        min_Consumption_and_Decipation = historical_data['Consumption and Dicipation'].min()
        max_Consumption_and_Decipation = historical_data['Consumption and Dicipation'].max()


        date_formatted = date.strftime('%Y-%m-%d %H:%M:%S')  # Format date as 'YYYY-MM-DD HH:MM:SS'
        # Generate random values within the historical range
        random_Solar_Gird_Generation = np.random.uniform(min_Solar_Gird_Generation, max_Solar_Gird_Generation)
        random_Consumption_and_Decipation = np.random.uniform(min_Consumption_and_Decipation, max_Consumption_and_Decipation)
        # Calculate total consumption and total price
        Solar_Saving_and_Battry_backup_value = max(random_Solar_Gird_Generation - random_Consumption_and_Decipation,0)

        # Append generated data to lists
        dates.append(date_formatted)
        Solar_Gird_Generation.append(random_Solar_Gird_Generation)
        Consumption_and_Decipation.append(random_Consumption_and_Decipation)
        Solar_Saving_and_Battry_backup.append(Solar_Saving_and_Battry_backup_value)

    # Create a DataFrame from the generated data
    generated_data = pd.DataFrame({
        'Date': dates,
        'Solar Gird Generation': Solar_Gird_Generation,
        'Consumption and Dicipation': Consumption_and_Decipation,
        'Solar Saving and backup': Solar_Saving_and_Battry_backup
    })

    return generated_data


def update_solar_data(file_Path):
    data = pd.read_excel(file_Path)
    end_date = datetime.now()
    start_date = max(data['Date'])
    # Extracting only the date part (year, month, day) from the datetime objects
    start_date_date = start_date.date()
    end_date_date = end_date.date()

    # Comparing dates
    if start_date_date != end_date_date:
        generated_data = generate_random_data_for_Solar(start_date, end_date, data)
        solar_data = pd.concat([data, generated_data], ignore_index=True)
        solar_data.to_excel(file_Path)


def add_solar_consumption(file_Path, max_range=4):
    data = pd.read_excel(file_Path)
    data['Date'] = pd.to_datetime(data['Date'])
    # Sort DataFrame by 'Date' column in descending order
    df_sorted = data.sort_values(by='Date', ascending=False)
    latest_row_index = df_sorted.index[0]
    df_sorted.at[latest_row_index, 'Solar Gird Generation'] += np.random.randint(df_sorted.at[latest_row_index, 'Solar Gird Generation'],
                                                                        df_sorted.at[
                                                                            latest_row_index, 'Solar Gird Generation'] + max_range)
    df_sorted.at[latest_row_index, 'Consumption and Dicipation'] += np.random.randint(df_sorted.at[latest_row_index, 'Consumption and Dicipation'],
                                                                       df_sorted.at[
                                                                           latest_row_index, 'Consumption and Dicipation'] + max_range)

    df_sorted.at[latest_row_index, 'Solar Saving and backup'] = max(0,df_sorted.at[latest_row_index, 'Solar Gird Generation'] - df_sorted.at[
        latest_row_index, 'Consumption and Dicipation'])

    df_sorted['Date'] = pd.to_datetime(df_sorted['Date'])
    df_sorted.to_excel(file_Path, index=False)
