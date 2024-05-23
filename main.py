import base64
from datetime import datetime, timedelta
import streamlit as st
import time
import sqlite3
from Data_pulling import generate_random_data_for_over_consumption, update_consumption_data, add_random_consumption, \
    generate_random_data_for_households, add_households_consumption, generate_random_data_for_Solar, \
    add_solar_consumption, update_households_data, update_solar_data
from passlib.hash import pbkdf2_sha256
import re
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
import plotly.graph_objects as go
import numpy as np
import statsmodels.api as sm
import plotly.express as px
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
import pandas as pd
from langchain_openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
user_good_name=""
image_data=""
overall_consumption_data=None
house_holds_data=None
solar_data=None

try:
    overall_consumption_data = pd.read_excel(f"Data/{st.session_state.username}-over-consumption.xlsx")
    overall_consumption_data['Date'] = pd.to_datetime(overall_consumption_data['Date'])
    update_consumption_data(f"Data/{st.session_state.username}-over-consumption.xlsx")

    house_holds_data = pd.read_excel(f"Data/{st.session_state.username}-households-data.xlsx")
    house_holds_data['Date'] = pd.to_datetime(house_holds_data['Date'])
    update_households_data(f"Data/{st.session_state.username}-households-data.xlsx")

    solar_data = pd.read_excel(f"Data/{st.session_state.username}-solar-data.xlsx")
    solar_data['Date'] = pd.to_datetime(solar_data['Date'])
    update_solar_data(f"Data/{st.session_state.username}-solar-data.xlsx")
except:
    pass

# Create a SQLite database connection
conn = sqlite3.connect('Database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        good_name TEXT,
        contact_gmail TEXT,
        profile TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')


if hasattr(st.session_state, "logged_in") and st.session_state.logged_in and not hasattr(st.session_state, "isGenerated"):
    end_date = datetime.now()
    try:
        overall_consumption_data = pd.read_excel(f"Data/{st.session_state.username}-over-consumption.xlsx")
        house_holds_data = pd.read_excel(f"Data/{st.session_state.username}-households-data.xlsx")
        solar_data = pd.read_excel(f"Data/{st.session_state.username}-solar-data.xlsx")
    except:
        overall_consumption_data = pd.read_excel(f"Data/Consumption_data.xlsx")
        start_date = end_date - timedelta(days=120)  # Previous 3 year months
        generated_data = generate_random_data_for_over_consumption(start_date, end_date, overall_consumption_data)
        overall_consumption_data =generated_data #pd.concat([overall_consumption_data, generated_data], ignore_index=True)
        overall_consumption_data['Date'] = pd.to_datetime(overall_consumption_data['Date'])
        overall_consumption_data.to_excel(f'Data/{st.session_state.username}-over-consumption.xlsx',index=False)

        house_holds_data = pd.read_excel(f"Data/households_data.xlsx")
        start_date = end_date - timedelta(days=120)  # Previous 3 year months
        generated_data = generate_random_data_for_households(start_date, end_date, house_holds_data)
        house_holds_data = generated_data  # pd.concat([overall_consumption_data, generated_data], ignore_index=True)
        house_holds_data['Date'] = pd.to_datetime(house_holds_data['Date'])
        house_holds_data.to_excel(f"Data/{st.session_state.username}-households-data.xlsx",index=False)

        solar_data = pd.read_excel(f"Data/Solar_Consumption_and_Dataset.xlsx")
        start_date = end_date - timedelta(days=120)  # Previous 3 year months
        generated_data = generate_random_data_for_Solar(start_date, end_date, solar_data)
        solar_data = generated_data  # pd.concat([overall_consumption_data, generated_data], ignore_index=True)
        solar_data['Date'] = pd.to_datetime(solar_data['Date'])
        solar_data.to_excel(f"Data/{st.session_state.username}-solar-data.xlsx", index=False)

        st.session_state.isGenerated=True

def run_chain(agent,query):
    return agent.invoke(query)

def delete_user_by_email(email):
    try:
        # Define the delete query
        delete_query = '''
            DELETE FROM users
            WHERE contact_gmail = ?
        '''
        cursor.execute(delete_query, (email,))
        # Commit the changes to the database
        conn.commit()

        return f"Account Deleted successfully."

    except sqlite3.Error as e:
        return "Error deleting user: {e}"

# Function to register a new user
def register(image_data,username, password, good_name, contact_gmail):
    hashed_password = pbkdf2_sha256.hash(password)
    cursor.execute('''
        INSERT INTO users (username, password, good_name,contact_gmail, profile)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, hashed_password, good_name, contact_gmail,image_data))
    conn.commit()

# Function to validate password
def is_valid_password(password):
    # Minimum length of 8 characters
    if len(password) < 8:
        return False

    # At least one uppercase letter
    if not any(char.isupper() for char in password):
        return False

    # At least one number
    if not any(char.isdigit() for char in password):
        return False

    # At least one special character
    special_characters = r'[!@#$%^&*(),.?":{}|<>]'
    if not re.search(special_characters, password):
        return False

    # If all criteria are met, the password is valid
    return True

# Function to authenticate a user
def authenticate(username, password):
    cursor.execute('SELECT password, good_name FROM users WHERE contact_gmail = ?', (username,))
    result = cursor.fetchone()
    if result:
        hashed_password = result[0]
        return pbkdf2_sha256.verify(password, hashed_password),result[1]
    return False,""

# Function to check if a username exists
def is_username_taken(username):
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()[0]
    conn.commit()
    return result > 0

# Function to check if a Gmail address is already registered
def is_gmail_taken(gmail):
    cursor.execute('SELECT COUNT(*) FROM users WHERE contact_gmail = ?', (gmail,))
    result = cursor.fetchone()[0]
    conn.commit()
    return result > 0

def Login():
    global user_good_name

    st.header("Sign In to Your Account")
    # Input fields for login
    with st.form("login_form"):
        login_username = st.text_input("Your email address")
        login_password = st.text_input("Password", type="password")
        # Login button
        if st.form_submit_button("Get Logged In"):
            if login_username and login_password:
                isauthenticated,user_good_name=authenticate(login_username, login_password)
                if isauthenticated:
                        st.success(f"Welcome {user_good_name}, You are Being Logged In!")
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.session_state.user_good_name = user_good_name
                        time.sleep(2)
                        st.rerun()
                else:
                    st.error("Login failed. Please check your credentials or there might exist account with such credentials.")

            else:
                st.warning("Please Fill all the Fields and Try Again.")

def Register():

    st.header("Register Your Account")
    with st.form("profile_form"):
        # Input fields for registration
        profile_image= st.file_uploader("Upload Profile", type=["jpg", "jpeg", "png"])
        register_username = st.text_input("Username")
        good_name = st.text_input("Good Name")
        contact_gmail = st.text_input("Your Gmail")
        validation_message = """
        Password must meet the following criteria:
        - Minimum length of 8 characters.
        - At least one uppercase letter.
        - At least one number.
        - At least one special character (e.g., !@#$%^&*(),.?":{}|<>).
        Please ensure your password adheres to these requirements for increased security.
        """
        st.write(validation_message)
        register_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        register_button=st.form_submit_button('Register Account')
                # Validate inputs and register button
        if register_button:
            if is_username_taken(register_username):
                st.error("Username already taken. Please choose a different username.")
                return
            if is_gmail_taken(contact_gmail):
                st.error("Gmail address already registered. Please use a different Gmail address.")
                return

            if (profile_image and register_username and register_password and confirm_password and good_name  and contact_gmail):
                if register_password == confirm_password and is_valid_password(register_password):
                    image_data = None
                    if profile_image:
                        # Convert the image to base64 and store it
                        image_data = base64.b64encode(profile_image.read()).decode("utf-8")
                    register(image_data,register_username,register_password,good_name,contact_gmail)
                    st.success("Registration successful! You can now login.")
                else:
                    st.error(
                                "Password and confirm password do not match or do not meet the criteria."
                            )
            else:
                st.warning("Please fill in all the fields along with Profile Image.")

def home():
    st.image("Images/Lgo-Image-Eletric.png", width=50)
    st.title("Unlock the power of informed energy management")
    st.write(
        "Gain comprehensive visibility into your household's energy consumption and dissipation patterns with our advanced dashboard. Effortlessly track usage trends, identify areas for optimization, and take control of your energy footprint to maximize efficiency and savings. Experience the synergy of data-driven insights and intuitive interface, empowering you to make smarter choices for a greener, more sustainable future.")

def get_user_profile_by_email(email_address):

    cursor.execute('''
        SELECT username,good_name,profile,timestamp
        FROM users
        WHERE contact_gmail = ?
    ''', (email_address,))
    user_profile = cursor.fetchone()
    if user_profile:
        # User profile found
        return {
            'username': user_profile[0],
            'good_name': user_profile[1],
            'contact_gmail':email_address,
            'profile':user_profile[2],
            'timestamp':user_profile[3],
        }
    else:
        # User profile not found
        return None

def profile():
    if hasattr(st.session_state, "logged_in") and st.session_state.logged_in:
        st.title("My Profile")
        st.write("Edit Your Profile Information with ease.")
        st.markdown("---")
        # Get the user email from the session variable (replace with your session logic)
        user_email = st.session_state.username
        if not user_email:
            st.error("User email not found in session.")
            return
        # Retrieve user profile information based on email
        user_profile = get_user_profile_by_email(user_email)
        if user_profile is None:
            st.error("User not found.")
            return
        # Use st.form for a more organized layout
        with st.form("profile_form"):
            # Allow the user to view or edit their profile using a single text input

            image_data = base64.b64decode(user_profile['profile'])
            hover_code = """
                        <style>
                        .image-holder 
                        {
                            text-align:center;
                            margin-bottom:30px;
                        }
                        .image
                        {
                        border-radius:50%;
                        width:20%;
                        cursor:pointer;
                        }
                            .image:hover {

                                transform: scale(1.3);  /* You can adjust the scale factor as needed */
                                background-color:rgba(244,85,85,255);
                                transition:0.5s all;

                            }
                           .msg-hovering:hover
                           {
                           cursor:pointer;
                           transform:scale(0.95);
                           transition:0.3 s all;
                           }
                        </style>
                        """
            image_code = hover_code + f'<div class="image-holder" ><img class="image" src="data:image/png;base64,{base64.b64encode(image_data).decode()}" alt="{user_profile["good_name"]} Profile" ></div>'
            st.markdown(image_code, unsafe_allow_html=True)
            st.subheader("Information")
            edited_contact_gmail = st.text_input("Contact Gmail", value=user_profile['contact_gmail'], disabled=True)
            edited_timeStamp = st.text_input("Account Creation Time Stamp", value=user_profile['timestamp'],
                                             disabled=True)

            edited_user_name = st.text_input("User Name", value=user_profile['username'])
            edited_good_name = st.text_input("Good Name", value=user_profile['good_name'])
            col1, col2 = st.columns([1, 1])
            with col1:
                update_button = st.form_submit_button("Update Profile with Latest Information",
                                                      use_container_width=True)
                if update_button:
                    if edited_user_name and edited_good_name  and edited_contact_gmail:
                        update_profile(edited_user_name, edited_good_name, edited_contact_gmail)
                        st.success("Profile updated successfully!")
                    else:
                        st.warning('Please Fill all the Fields and Do not Leave them Empty.')
            with col2:
                delete_button = st.form_submit_button("Delete My Account", use_container_width=True)
                if delete_button:
                    results = delete_user_by_email(st.session_state.username)
                    st.error(f'Sorry to See you Go. ({results})')
                    st.session_state.logged_in = False
                    st.session_state.username = None
                    time.sleep(1)
                    st.rerun()
    else:
        st.title("Please Login with Appropriate Account")

def update_profile(edited_user_name,edited_good_name, edited_contact_gmail ):
    cursor.execute('''
            UPDATE users
            SET username=?,good_name = ?
            WHERE contact_gmail = ?
        ''', (edited_user_name,edited_good_name,edited_contact_gmail))
    conn.commit()

def logout():
    st.title("Account Session Revoking")
    st.write("Logging out of Your Account in progress.")
    if hasattr(st.session_state, "logged_in") and st.session_state.logged_in:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.clear()
        st.success("You are Being logged out!")
        time.sleep(2)
        st.rerun()
    else:
        st.sidebar.info("Please login or register.")

def Interact_with_My_Data_using_AI():
    st.title("Interact with your Data using AI")
    st.write("Ask complex Aggregated and Critical Queestion to the AI to get Answers from User Data.")
    st.code(
        "User Question- Tell me week days i should do the laundary to save energy? \nAI Agent- it will repsond like The best days to do the laundry to save energy, based on the average solar saving and battery backup, are Sunday, Friday, and Thursday. These days have the highest average solar saving and battery backup, which means that the solar grid generation is more than the consumption and dissipation, hence more energy is saved.")

    filter = st.selectbox("Select Data to Chat with", ("Solar Consumption and Dicipation", "Electricity Consumption", "Household Devices Consumption"), index=2)
    if filter=="Solar Consumption and Dicipation":
        filepath=f"Data/{st.session_state.username}-solar-data.xlsx"
    elif filter=="Electricity Consumption":
        filepath=f"Data/{st.session_state.username}-over-consumption.xlsx"
    elif filter=="Household Devices Consumption":
        filepath=f"Data/{st.session_state.username}-households-data.xlsx"

    data=pd.read_excel(filepath)
    agent = create_pandas_dataframe_agent(
        ChatOpenAI(temperature=0, model="gpt-4"),
        data,
        verbose=False,
        agent_type=AgentType.OPENAI_FUNCTIONS,
    )
    input_text = st.text_input(f"Ask any Question to AI about {filter} Data")
    getans = st.button("Get Answer", use_container_width=True)
    if getans:
        result = run_chain(agent, input_text)
        st.code(result['output'])

def overall_consumption():
    overall_consumption_data['Date'] = pd.to_datetime(overall_consumption_data['Date'])
    refresh = st.button("Refresh Consumption Dashboard", use_container_width=True)
    if refresh:
        add_random_consumption(f"Data/{st.session_state.username}-over-consumption.xlsx")
        st.rerun()

    def aggregate_consumption(df, time_period):
        # Convert 'Date' column to datetime type if it's not already
        df['Date'] = pd.to_datetime(df['Date'])
        # Define grouping columns based on the specified time period
        if time_period == 'Yearly':
            group_cols = df['Date'].dt.year.rename('Year')
        elif time_period == 'Monthly':
            group_cols = [df['Date'].dt.year.rename('Year'), df['Date'].dt.month.rename('Month')]
        elif time_period == 'Weekly':
            group_cols = [df['Date'].dt.year.rename('Year'), df['Date'].dt.month.rename('Month'),
                          df['Date'].dt.isocalendar().week.rename('Week')]
        else:  # Daily
            group_cols = df['Date'].rename('Date')

        # Perform aggregation based on the time period
        aggregated_df = df.groupby(group_cols).agg({
            'Daylight Consumption in kWh': 'sum',
            'Night Consumption in kWh': 'sum'
        }).reset_index()

        # Optionally, rename the index columns after resetting to prevent any conflict
        if 'Date' in df.columns and 'Date' in aggregated_df.columns:
            aggregated_df.rename(columns={'Date': 'Date'}, inplace=True)

        if time_period == 'Yearly':
            aggregated_df['Date'] = "Year (" + aggregated_df['Year'].astype(str) + ")"
        elif time_period == 'Weekly':
            aggregated_df['Date'] = "Year (" + aggregated_df['Year'].astype(str) + ")" + "-" + "Month (" + \
                                    aggregated_df[
                                        'Month'].astype(str) + ")" + "-" + "Week (" + aggregated_df['Week'].astype(
                str) + ")"
        elif time_period == 'Monthly':
            aggregated_df['Date'] = "Year (" + aggregated_df['Year'].astype(str) + ")" + "-" + "Month (" + \
                                    aggregated_df[
                                        'Month'].astype(str) + ")"

        return aggregated_df

    def get_upcoming_dates(num_days):
        upcoming_dates = []
        today = datetime.today()
        for i in range(num_days):
            next_date = today + timedelta(days=i + 1)
            upcoming_dates.append(next_date.strftime('%Y-%m-%d'))
        return upcoming_dates

    def generate_pie_chart(df):
        # Calculate total consumption for each type
        total_daylight = df['Daylight Consumption in kWh'].sum()
        total_night = df['Night Consumption in kWh'].sum()

        # Create a DataFrame for the pie chart
        pie_df = pd.DataFrame({'Type': ['Daylight', 'Night'], 'Consumption': [total_daylight, total_night]})

        # Use Plotly to create the pie chart
        fig = px.pie(pie_df, names='Type', values='Consumption', title='Daylight vs Night Consumption Distribution in KWh')

        # Display the chart using Streamlit
        st.plotly_chart(fig)

    st.title("Day and Night Time Consumption and Cost Analysis")
    st.write(
        "Dashboard displays the Data Analytics for the Day time and Night TIme Electricity Consumption and analytics and trends with time.\n\n\n\n\n.")

    dates, sliders = st.columns([1, 1])


    with dates:
        start_date = st.date_input('Start Date', overall_consumption_data['Date'].min())
        end_date = st.date_input('End Date', overall_consumption_data['Date'].max())

    with sliders:
        daylight_min = overall_consumption_data['Daylight Consumption in kWh'].min()
        daylight_max = overall_consumption_data['Daylight Consumption in kWh'].max()
        night_min = overall_consumption_data['Night Consumption in kWh'].min()
        night_max = overall_consumption_data['Night Consumption in kWh'].max()

        daylight_range = st.slider('Select Daylight Consumption Range (kWh)', daylight_min, daylight_max,
                                   (daylight_min, daylight_max))
        night_range = st.slider('Select Night Consumption Range (kWh)', night_min, night_max,
                                (night_min, night_max))

    col34,col33=st.columns([1,1])
    with col34:
        data_type = st.selectbox("Select Data Type", ("Daylight", "Night", "All"), index=2)
    with col33:
        time_perioed = st.selectbox("Select Period Type", ("Daily", "Weekly", "Monthly","Yearly"), index=2)

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    if data_type == "All":
        day_filtered_data = overall_consumption_data[(overall_consumption_data['Date'] >= start_date) &
                                                     (overall_consumption_data['Date'] <= end_date) &
                                                     (overall_consumption_data['Daylight Consumption in kWh'] >=
                                                      daylight_range[0]) &
                                                     (overall_consumption_data['Daylight Consumption in kWh'] <=
                                                      daylight_range[1])]
        night_filtered_data = overall_consumption_data[(overall_consumption_data['Date'] >= start_date) &
                                                       (overall_consumption_data['Date'] <= end_date) &
                                                       (overall_consumption_data['Night Consumption in kWh'] >=
                                                        night_range[0]) &
                                                       (overall_consumption_data['Night Consumption in kWh'] <=
                                                        night_range[1])]
        filtered_dataa = pd.concat([day_filtered_data, night_filtered_data])
        aggregated_df = aggregate_consumption(filtered_dataa, time_perioed)

        fig = px.line(aggregated_df, x='Date', y=['Daylight Consumption in kWh', 'Night Consumption in kWh'],
                      labels={'value': 'Consumption (kWh)'}, title='Daylight and Night Consumption over Time')
        fig.update_xaxes(rangeslider_visible=True)
        # Customize layout
        fig.update_layout(xaxis_title='Date', yaxis_title='Consumption (kWh)', xaxis_tickangle=-45,height=600)

        fig = px.line(aggregated_df, x='Date', y=['Daylight Consumption in kWh', 'Night Consumption in kWh'],
                      labels={'value': 'Consumption (kWh)'}, title='Daylight and Night Consumption over Time')
        fig.update_xaxes(rangeslider_visible=True)
        # Customize layout
        fig.update_layout(xaxis_title='Date', yaxis_title='Consumption (kWh)', xaxis_tickangle=-45, height=600)

        # Display plot using Streamlit

        # Generate pie chart

        # Display plot using Streamlit

    elif data_type == "Daylight":
        filtered_dataa = overall_consumption_data[(overall_consumption_data['Date'] >= start_date) &
                                                 (overall_consumption_data['Date'] <= end_date) &
                                                 (overall_consumption_data['Daylight Consumption in kWh'] >=
                                                  daylight_range[0]) &
                                                 (overall_consumption_data['Daylight Consumption in kWh'] <=
                                                  daylight_range[1])]
        aggregated_df = aggregate_consumption(filtered_dataa, time_perioed)

        fig = px.line(aggregated_df, x='Date',
                      y='Daylight Consumption in kWh' if data_type == "Daylight" else 'Night Consumption in kWh',
                      labels={'value': 'Consumption (kWh)', 'Date': 'Date'},
                      title=f'{data_type} Consumption over Time')
        fig.update_xaxes(rangeslider_visible=True)

    elif data_type == "Night":
        filtered_dataa = overall_consumption_data[(overall_consumption_data['Date'] >= start_date) &
                                                 (overall_consumption_data['Date'] <= end_date) &
                                                 (overall_consumption_data['Night Consumption in kWh'] >=
                                                  night_range[0]) &
                                                 (overall_consumption_data['Night Consumption in kWh'] <=
                                                  night_range[1])]
        aggregated_df = aggregate_consumption(filtered_dataa, time_perioed)

        fig = px.line(aggregated_df, x='Date',
                      y='Daylight Consumption in kWh' if data_type == "Daylight" else 'Night Consumption in kWh',
                      labels={'value': 'Consumption (kWh)', 'Date': 'Date'},
                      title=f'{data_type} Consumption over Time')
        fig.update_xaxes(rangeslider_visible=True)

    overall_consumption_data['Date'] = pd.to_datetime(overall_consumption_data['Date'])
    # Calculate metrics
    avg_daylight_consumption = overall_consumption_data['Daylight Consumption in kWh'].mean()
    avg_night_consumption = overall_consumption_data['Night Consumption in kWh'].mean()
    avg_daylight_price = overall_consumption_data['Daylight Price in UAH'].mean()
    avg_night_price = overall_consumption_data['Night Price in UAH'].mean()
    total_consumption = overall_consumption_data[
        ['Daylight Consumption in kWh', 'Night Consumption in kWh']].sum().sum()
    total_price = overall_consumption_data[['Daylight Price in UAH', 'Night Price in UAH']].sum().sum()
    day_night_consumption_ratio = avg_daylight_consumption / avg_night_consumption
    day_night_price_ratio = avg_daylight_price / avg_night_price
    # Calculate percentage metrics
    percent_daylight_consumption = (avg_daylight_consumption / total_consumption) * 100
    percent_night_consumption = (avg_night_consumption / total_consumption) * 100
    percent_daylight_price = (avg_daylight_price / total_price) * 100
    percent_night_price = (avg_night_price / total_price) * 100

    st.markdown('---')
    col1,col2,=st.columns([1,1])
    with col1:
        st.subheader("Data Corelation and Description")
        st.write(filtered_dataa.drop(['Month','Year','Date'],axis=1).describe())
    with col2:
        st.subheader("Filtered Data")
        st.write(filtered_dataa,height=90)
    # Display metrics using Streamlit
    st.title('Electricity Consumption and Pricing Metrics\n\n.')
    col1,col2,col3,col4,col5,col6=st.columns([1,1,1,1,1,1])
    col7,col8,col9,col10,col11,col12=st.columns([1,1,1,1,1,1])

    st.title("Day Time Cost ( 2.64 UAH ) Night Time Cost ( 1.32 UAH )")
    with col1:
        st.metric("Average Daylight Consumption (kWh)", round(avg_daylight_consumption, 2))
    with col2:
        st.metric("Average Night Consumption (kWh)", round(avg_night_consumption, 2))
    with col3:
        st.metric("Average Daylight Price (UAH)", round(avg_daylight_price, 2))
    with col4:
        st.metric("Average Night Price (UAH)", round(avg_night_price, 2))
    with col5:
        st.metric("Total Consumption (kWh)", round(total_consumption, 2))
    with col6:
        st.metric("Total Price (UAH)", round(total_price, 2))
    with col7:
        st.metric("Daylight to Night Consumption Ratio", round(day_night_consumption_ratio, 2))
    with col8:
        st.metric("Daylight to Night Price Ratio", round(day_night_price_ratio, 2))
    with col9:
        st.metric("Percentage of Daylight Consumption",  round(percent_daylight_consumption, 2), "%")
    with col10:
        st.metric("Percentage of Night Consumption",  round(percent_night_consumption, 2), "%")
    with col11:
        st.metric("Percentage of Daylight Price",  round(percent_daylight_price, 2), "%")
    with col12:
        st.metric("Percentage of Night Price",  round(percent_night_price, 2), "%")
    st.markdown('---')

    col13, col14 = st.columns([1, 1])
    with col13:
        st.plotly_chart(fig, use_container_width=True)
    with col14:
        generate_pie_chart(filtered_dataa)

    # Prepare data for modeling

    st.markdown('---')
    # Display results in Streamlit
    st.title('Monthly Energy Consumption Cost and Forecast\n\n\n.')
    number_of_month = st.slider('Select Number of Months to be Predicted for Approximate Cost', 0, 12,
                                5)

    # Create a date index
    overall_consumption_data['Date'] = pd.to_datetime(overall_consumption_data[['Year', 'Month']].assign(DAY=1))
    overall_consumption_data.set_index('Date', inplace=True)

    # Prepare data for SARIMA model
    monthly_costs = overall_consumption_data['Total Price'].resample('M').sum()

    current_month_cost=monthly_costs[-1]

    # Exclude the current month's data
    current_month = monthly_costs.index[-1].strftime('%Y-%m')
    historical_costs = monthly_costs.loc[:monthly_costs.index[-2].strftime('%Y-%m')]

    order = (1, 1, 1)  # SARIMA order (p, d, q)
    seasonal_order = (1, 1, 1, 12)  # Seasonal order (P, D, Q, s)
    sarima_model = sm.tsa.statespace.SARIMAX(historical_costs, order=order, seasonal_order=seasonal_order)
    fitted_sarima_model = sarima_model.fit()

    # Predict the next 5 months
    forecast = fitted_sarima_model.forecast(steps=number_of_month)

    # Ensure non-negative predictions
    forecast[forecast < 0] = 0

    # Extract month names and years
    month_names = forecast.index.strftime('%B')
    years = forecast.index.year

    st.metric("\n\nCurrent Month Cost so far ", f"UAH {round(current_month_cost,2)} ")
    cols = {"col1": st.columns(number_of_month)}
    # Show metrics
    for i in range(1, number_of_month+1):
        with cols['col1'][i - 1]:
            predicted_cost = forecast[i - 1]
            previous_cost = forecast[i - 2] if i > 1 else None
            trend_color=""
            if previous_cost is not None:
                if predicted_cost > previous_cost:
                    trend_color = "%"
                elif predicted_cost < previous_cost:
                    trend_color = "-%"
                else:
                    trend_color = "%"

                st.metric(f"Predicted Cost Month {month_names[i - 1]} {years[i - 1]}",
                          f"UAH {predicted_cost:.2f} ",
                          trend_color)
            else:
                st.metric(f"Predicted Cost Current Month {month_names[i - 1]} {years[i - 1]}",
                          f"UAH {predicted_cost:.2f}",
                          trend_color)

    st.markdown('---')
    st.write("### Historical Data and Predictions ")
    col1,col2=st.columns([1,1])
    # Plot historical data and prediction
    with col1:
        fig, ax = plt.subplots()
        ax.plot(historical_costs.index, historical_costs, label='Historical Monthly Costs')
        forecast_index = pd.date_range(start=historical_costs.index[-1], periods=number_of_month+1, freq='M')[1:]  # Next 5 months
        ax.plot(forecast_index, forecast, 'ro', label='Forecasted Cost')
        ax.set_title('Monthly Energy Costs and Forecast')
        ax.set_xlabel('Month')
        ax.set_ylabel('Total Cost (UAH)')
        ax.legend()
        # Convert matplotlib figure to Plotly figure
        plotly_fig = go.Figure()
        for trace in ax.get_lines():
            x = trace.get_xdata()
            y = trace.get_ydata()
            plotly_fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=trace.get_label()))

        # Convert x-axis to date format
        plotly_fig.update_xaxes(type='date')

        # Display Plotly figure in Streamlit
        st.plotly_chart(plotly_fig)

    with col2:
        # Display bar chart for historical data and predictions
        bar_chart_data = pd.DataFrame({'Date': forecast_index, 'Predicted Cost': forecast})

        # Plot bar chart
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=month_names, y=bar_chart_data['Predicted Cost'], name='Predicted Cost'))
        fig_bar.update_layout(barmode='group', xaxis_title='Month', yaxis_title='Total Cost (UAH)',
                              title='Historical Data and Predictions for Next 5 Months')
        st.plotly_chart(fig_bar)

    st.markdown('---')
    # Display results in Streamlit
    st.title('Daily Energy Consumption Cost and Forecast\n\n\n.')
    number_of_days = st.slider('Select Number of Days to be Predicted for Approximate Cost', 0, 30, 7)

    # Reset index to ensure unique labels
    overall_consumption_data.reset_index(drop=True, inplace=True)

    # Exclude the current day's data
    historical_costs = overall_consumption_data['Total Price'][:-1]

    # Get the last date in the historical data
    last_date = historical_costs.index[-1]

    # Prepare historical data for forecasting
    historical_data = overall_consumption_data.loc[:last_date]
    # SARIMA model setup
    order = (1, 1, 1)  # SARIMA order (p, d, q)
    seasonal_order = (1, 1, 1, 12)  # Seasonal order (P, D, Q, s)
    sarima_model = sm.tsa.statespace.SARIMAX(historical_data['Total Price'], order=order, seasonal_order=seasonal_order)
    fitted_sarima_model = sarima_model.fit()

    # Predict the next 'number_of_days' days
    forecast = fitted_sarima_model.forecast(steps=number_of_days)
    # Ensure non-negative predictions
    forecast[forecast < 0] = 0

    # Extract day names and years
    forecast_index = pd.date_range(start=get_upcoming_dates(len(forecast))[0], periods=number_of_days, freq='D')
    day_names = forecast_index.strftime('%A')
    st.metric(f"\n\nCurrent Day Cost so far", f"UAH {round(float(overall_consumption_data['Total Price'].iloc[-1]), 2)}")
    cols = st.columns(number_of_days)
    # Show metrics
    forecast=list(forecast)
    for i in range(number_of_days):
        predicted_cost = forecast[i]
        previous_cost = forecast[i - 1] if i > 0 else None
        trend_color = ""
        if previous_cost is not None:
            if predicted_cost > previous_cost:
                trend_color = "%"
            elif predicted_cost < previous_cost:
                trend_color = "-%"
            else:
                trend_color = "%"

            cols[i].metric(f"Predicted Cost Day {day_names[i]}",
                           f"UAH {predicted_cost:.2f}",
                           f"{trend_color}")
        else:
            cols[i].metric(f"Predicted Cost  Day {day_names[i]}",
                           f"UAH {predicted_cost:.2f}",
                           f"{trend_color}")

    st.markdown('---')
    st.write("### Historical Data and Predictions ")
    col1, col2 = st.columns([1, 1])
    # Plot historical data and prediction
    with col1:
        fig, ax = plt.subplots()
        ax.plot(historical_costs.index, historical_costs, label='Historical Daily Costs')
        ax.plot(forecast_index, forecast, 'ro', label='Forecasted Cost')
        ax.set_title('Daily Energy Costs and Forecast')
        ax.set_xlabel('Date')
        ax.set_ylabel('Total Cost (UAH)')
        ax.legend()
        # Convert matplotlib figure to Plotly figure
        plotly_fig = go.Figure()
        for trace in ax.get_lines():
            x = trace.get_xdata()
            y = trace.get_ydata()
            plotly_fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=trace.get_label()))

        # Convert x-axis to date format
        plotly_fig.update_xaxes(type='date')
        # Display Plotly figure in Streamlit
        st.plotly_chart(plotly_fig)

    with col2:
        # Display bar chart for historical data and predictions
        bar_chart_data = pd.DataFrame({'Date': forecast_index, 'Predicted Cost': forecast})

        # Plot bar chart
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=forecast_index, y=bar_chart_data['Predicted Cost'], name='Predicted Cost'))
        fig_bar.update_layout(xaxis_title='Date', yaxis_title='Total Cost (UAH)',
                              title='Historical Data and Predictions for Next Days')
        st.plotly_chart(fig_bar)

    st.markdown('---')

    # time.sleep(10)
    # add_random_consumption(f"Data/{st.session_state.username}-over-consumption.xlsx")
    # st.rerun()

def house_hold_consumption():
        fig_stacked_bar=None
        def get_upcoming_dates(num_days):
            upcoming_dates = []
            today = datetime.today()
            for i in range(num_days):
                next_date = today + timedelta(days=i + 1)
                upcoming_dates.append(next_date.strftime('%Y-%m-%d'))
            return upcoming_dates
        refresh = st.button("Refresh Houses Holds Dashboard", use_container_width=True)
        if refresh:
            add_households_consumption(f"Data/{st.session_state.username}-households-data.xlsx")
            st.rerun()
        house_holds_data['Date'] = pd.to_datetime(house_holds_data['Date'])
        filtered_data = house_holds_data

        st.title("Household Devices Electricity Consumption")
        st.write("Dashboard displays the Data Analytics for household devices.\n\n\n\n\n.")

        # Convert 'Date' column to datetime


        # Filter options
        devices = house_holds_data.columns[1:-1]
        devices = ['All Devices'] + list(devices)
        selected_item = st.selectbox("Select Household Item", devices, index=0)
        col1,col2=st.columns([1,1])
        with col1:
            start_date = st.date_input("Start Date", house_holds_data['Date'].min())
        with col2:
            end_date = st.date_input("End Date", house_holds_data['Date'].max())

        st.markdown('---')
        # Convert date inputs to datetime
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)



        # Filter data based on selected item and date range
        if selected_item == 'All Devices':
            filtered_data = house_holds_data[(house_holds_data['Date'] >= start_date) & (house_holds_data['Date'] <= end_date)]
            # Line chart showing usage over time for all devices
            fig = px.line(filtered_data, x='Date', y=filtered_data.columns[1:-1], title="Electricity Consumption of All Devices Over Time")

            # Bar plot showing total consumption of all devices over time
            total_consumption = filtered_data.drop(columns=['Date', 'total']).sum(axis=1)
            fig_bar = go.Figure(data=[go.Bar(x=filtered_data['Date'], y=total_consumption)])
            fig_bar.update_layout(title="Total Electricity Consumption in KWh of All Devices Over Time", xaxis_title="Date",
                                  yaxis_title="Consumption (KWh)")

            # Stacked bar plot showing consumption of individual devices
            fig_stacked_bar = go.Figure()
            for device in devices[1:]:
                fig_stacked_bar.add_trace(go.Bar(x=filtered_data['Date'], y=filtered_data[device], name=device))

            fig_stacked_bar.update_layout(barmode='stack', title="Electricity Consumption in KWh of Individual Devices Over Time",
                                          xaxis_title="Date", yaxis_title="Consumption (KWh)")
        else:
            updated_items = [x for x in devices if x != "All Devices" and x!= selected_item]
            filtered_data=house_holds_data.drop(updated_items,axis=1)
            filtered_data = filtered_data[(house_holds_data['Date'] >= start_date) & (filtered_data['Date'] <= end_date)]
            # Line chart showing usage over time for the selected item
            fig = px.line(filtered_data, x='Date', y=selected_item, title=f"{selected_item} Consumption in KWh Over Time")
        filtered_data['Date'] = pd.to_datetime(filtered_data['Date'])
            # Display additional metrics using st.metric
        st.metric("Total Energy Consumption", f"{round(filtered_data['total'].sum(), 2)} KWh")
        avg_daily_energy = filtered_data.drop('Date', axis=1).mean()
        st.subheader("Average Daily Energy")
        cols = {"col1": st.columns(len(avg_daily_energy))}
        counter = 1
            # Calculate average daily energy consumption per category
        for category, value in avg_daily_energy.items():
            with cols['col1'][counter - 1]:
                counter += 1
                st.metric(f"({category})", f"{round(value, 2)} KWh")

            # Identify peak energy consumption per day
        st.markdown('---')
        filtered_data['Peak Category'] = filtered_data.drop(['Date', 'total'], axis=1).idxmax(axis=1)
        peak_counts = filtered_data['Peak Category'].value_counts()
        st.subheader("Peak Energy Consumption")
        cols = {"col1": st.columns(len(peak_counts))}
        counter = 1
        for category, count in peak_counts.items():
            with cols['col1'][counter - 1]:
                counter += 1
                st.metric(f"({category})", f"{round(value, 2)} KWh")
        st.markdown('---')
        col1, col2, = st.columns([1, 1])
        with col1:
            st.subheader("Data Corelation and Description")
            st.write(filtered_data.drop([ 'Date'], axis=1).describe())
        with col2:
            st.subheader("Filtered Data")
            st.write(filtered_data, height=90)
        st.markdown('---')
        if fig_stacked_bar:
            st.plotly_chart(fig_stacked_bar, use_container_width=True)
        else:
            st.plotly_chart(fig,use_container_width=True)

        col1,col2=st.columns([1,1])
        # Pie chart showing participation of each item in total value
        with col1:
            total_values = filtered_data.drop(columns=['Date', 'total','Peak Category']).sum(axis=0)
            fig_pie = px.pie(values=total_values, names=total_values.index, title="House Holds Devices Electricity Consumption")
            st.plotly_chart(fig_pie)

        with col2:
            # Sum consumption values for each device
            device_sum =total_values
            device_sum_sorted = device_sum.sort_values(ascending=False)

            # Create horizontal bar plot
            fig = go.Figure(go.Bar(
                x=device_sum_sorted.values,
                y=device_sum_sorted.index,
                orientation='h',
                text=[f'{device}: {usage} KWh' for device, usage in zip(device_sum_sorted.index, device_sum_sorted.values)],
                textposition='auto'
            ))

            fig.update_layout(title="Total Consumption of Each Device",
                              xaxis_title="Total Consumption (KWh)",
                              yaxis_title="Devices",
                              yaxis_categoryorder='total ascending')

            # Display the plot using Streamlit
            st.plotly_chart(fig)

        st.markdown('---')
        # Display results in Streamlit
        st.title('House Holds Devices Consumption Forcast\n\n\n.')
        number_of_days = st.slider('Select Number of Days to be Predicted for Approximate Consumption of all Devices', 0, 30, 7)

        # Reset index to ensure unique labels
        house_holds_data.reset_index(drop=True, inplace=True)

        # Exclude the current day's data
        historical_costs = house_holds_data['total'][:-1]

        # Get the last date in the historical data
        last_date = historical_costs.index[-1]

        # Prepare historical data for forecasting
        historical_data = house_holds_data.loc[:last_date]
        # SARIMA model setup
        order = (1, 1, 1)  # SARIMA order (p, d, q)
        seasonal_order = (1, 1, 1, 12)  # Seasonal order (P, D, Q, s)
        sarima_model = sm.tsa.statespace.SARIMAX(historical_data['total'], order=order, seasonal_order=seasonal_order)
        fitted_sarima_model = sarima_model.fit()
        # Predict the next 'number_of_days' days
        forecast = fitted_sarima_model.forecast(steps=number_of_days)
        # Ensure non-negative predictions
        forecast[forecast < 0] = 0

        # Extract day names and years
        forecast_index = pd.date_range(start=get_upcoming_dates(len(forecast))[0], periods=number_of_days, freq='D')
        day_names = forecast_index.strftime('%A')
        st.metric(f"\n\nCurrent Day Devices Total Consumption so far", f"{round(float(house_holds_data['total'].iloc[-1]), 2)} KWh")
        cols = st.columns(number_of_days)
        # Show metrics
        forecast=list(forecast)
        for i in range(number_of_days):
            predicted_cost = forecast[i]
            previous_cost = forecast[i - 1] if i > 0 else None
            trend_color = ""
            if previous_cost is not None:
                if predicted_cost > previous_cost:
                    trend_color = "%"
                elif predicted_cost < previous_cost:
                    trend_color = "-%"
                else:
                    trend_color = "%"

                cols[i].metric(f"Predicted ( {day_names[i]} )",
                               f"{predicted_cost:.2f} (KWh)",
                               f"{trend_color}")
            else:
                cols[i].metric(f"Predicted ( {day_names[i]} )",
                               f"{predicted_cost:.2f} (KWh)",
                               f"{trend_color}")

        st.markdown('---')
        st.write("### Historical Data and Predictions ")
                # Display bar chart for historical data and predictions
        bar_chart_data = pd.DataFrame({'Date': forecast_index, 'Predicted consumpition': forecast})

            # Plot bar chart
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=forecast_index, y=bar_chart_data['Predicted consumpition'], name='Predicted consumpition'))
        fig_bar.update_layout(xaxis_title='Date', yaxis_title='Total consumption of all Devices (KWh)',
                                  title='Historical Data and Predictions for Next Days')
        st.plotly_chart(fig_bar,use_container_width=True)

def solar_dacipation():
    def get_upcoming_dates(num_days):
        upcoming_dates = []
        today = datetime.today()
        for i in range(num_days):
            next_date = today + timedelta(days=i + 1)
            upcoming_dates.append(next_date.strftime('%Y-%m-%d'))
        return upcoming_dates
    refresh = st.button("Refresh Solar Dashboard", use_container_width=True)
    if refresh:
        add_solar_consumption(f"Data/{st.session_state.username}-solar-data.xlsx")
        st.rerun()

    st.title("Solar Consumption and Saving")
    st.write(
            "Dashboard displays the Data Analytics for the Solar Power Generation, Dicipation and Saving.\n\n\n\n\n.")

    # Date range filter
    solar_data['Date'] = pd.to_datetime(solar_data['Date'])

    # Date range filter
    col1, col2 = st.columns([1, 1])
    with col1:
        start_date = st.date_input("Start Date", solar_data['Date'].min())
    with col2:
        end_date = st.date_input("End Date", solar_data['Date'].max())

    st.markdown('---')
    # Convert date inputs to datetime
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)


    filtered_data = solar_data[(solar_data['Date'] >= start_date) & (solar_data['Date'] <= end_date)]

    # Filter the data based on the selected date range
    # Calculate metrics

    average_solar_generation = filtered_data['Solar Gird Generation'].mean()
    average_consumption = filtered_data['Consumption and Dicipation'].mean()
    average_solar_saving = filtered_data['Solar Saving and backup'].mean()
    total_solar_generation = filtered_data['Solar Gird Generation'].sum()
    total_solar_saving = filtered_data['Solar Saving and backup'].sum()
    total_consumption = filtered_data['Consumption and Dicipation'].sum()
    peak_solar_generation = filtered_data.loc[filtered_data['Solar Gird Generation'].idxmax(), 'Solar Gird Generation']
    peak_consumption = filtered_data.loc[filtered_data['Consumption and Dicipation'].idxmax(), 'Consumption and Dicipation']
    peak_solar_saving = filtered_data.loc[filtered_data['Solar Saving and backup'].idxmax(), 'Solar Saving and backup']
    # Get the current date
    current_date = pd.to_datetime('today').date()

    # Filter data for the current day
    current_day_data = solar_data[solar_data['Date'].dt.date == current_date]
    current_day_solar_generation = current_day_data['Solar Gird Generation'].sum()
    current_day_solar_diciptation = current_day_data['Consumption and Dicipation'].sum()
    current_day_solar_saving = current_day_data['Solar Saving and backup'].sum()
    col00,col0,col000,col4=st.columns([1, 1, 1, 1])
    with col0:
        st.metric("Today Solar Generation so far", f"{round(current_day_solar_generation, 2)} KWh",
                  round((average_solar_generation / average_consumption) * 100, 2))
    with col00:
        st.metric("Today Solar Dicipation so far", f"{round(current_day_solar_diciptation, 2)} KWh",
                  round((average_solar_generation / average_consumption) * 100, 2))
    with col000:
        st.metric("Today Solar Saving", f"{round(current_day_solar_saving, 2)} KWh",
                  round((average_solar_generation / average_consumption) * 100, 2))
    with col4:
        st.metric("Overall Solar Efficiency", f"{round((total_solar_saving / total_solar_generation) * 100, 2) } KWh")

    st.markdown('---')
    col1, col2, col3, col5, col6, col7 = st.columns([1, 1, 1, 1, 1, 1])

    with col1:
        st.metric("Average Daily Solar Generation", f"{round(average_solar_generation, 2) } KWh",
              round((average_solar_generation / average_consumption) * 100, 2))
    with col2:
        st.metric("Average Daily Consumption", f"{round(average_consumption, 2) } KWh",
              round((average_consumption / average_solar_generation) * 100, 2))
    with col3:
        st.metric("Average Daily Solar Saving", f"{round(average_solar_saving, 2) } KWh",
              round((average_solar_saving / average_solar_generation) * 100, 2))

    with col5:
        st.metric("Peak Solar Generation Day",f"{ round(peak_solar_generation, 2) } KWh",
              round((peak_solar_generation / total_solar_generation) * 100, 2))
    with col6:
        st.metric("Peak Consumption Day", f"{round(peak_consumption, 2) } KWh",
              round((peak_consumption / total_consumption) * 100, 2))
    with col7:
        st.metric("Peak Solar Saving Day", f"{round(peak_solar_saving, 2) } KWh",
              round((peak_solar_saving / total_solar_saving) * 100, 2))

    st.markdown('---')
    col1,col2,=st.columns([1,1])
    with col1:
        st.subheader("Data Corelation and Description")
        st.write(filtered_data.drop(['Date'],axis=1).describe())
    with col2:
        st.subheader("Filtered Data")
        st.write(filtered_data,height=90)

    fig3 = px.bar(filtered_data, x='Date', y=['Solar Gird Generation', 'Consumption and Dicipation', 'Solar Saving and backup'],
                  title='Solar Generation, Consumption, and Savings on Specific Dates',
                  barmode='stack')
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('---')
        # Display results in Streamlit
    st.title('Solar Forcast\n\n\n.')
    number_of_days = st.slider('Select Number of Days to be Predicted for Approximate Generation', 0, 30, 7)
        # Reset index to ensure unique labels
    solar_data.reset_index(drop=True, inplace=True)

        # Exclude the current day's data
    historical_costs = solar_data['Solar Gird Generation'][:-1]

        # Get the last date in the historical data
    last_date = historical_costs.index[-1]

        # Prepare historical data for forecasting
    historical_data = solar_data.loc[:last_date]
        # SARIMA model setup
    order = (1, 1, 1)  # SARIMA order (p, d, q)
    seasonal_order = (1, 1, 1, 12)  # Seasonal order (P, D, Q, s)
    sarima_model = sm.tsa.statespace.SARIMAX(historical_data['Solar Gird Generation'], order=order, seasonal_order=seasonal_order)
    fitted_sarima_model = sarima_model.fit()
        # Predict the next 'number_of_days' days
    forecast = fitted_sarima_model.forecast(steps=number_of_days)
        # Ensure non-negative predictions
    forecast[forecast < 0] = 0

        # Extract day names and years
    forecast_index = pd.date_range(start=get_upcoming_dates(len(forecast))[0], periods=number_of_days, freq='D')
    day_names = forecast_index.strftime('%A')
    st.metric(f"\n\nCurrent Day Consumption so Generation", f"{round(float(solar_data['Solar Gird Generation'].iloc[-1]), 2)} KWh")
    cols = st.columns(number_of_days)
        # Show metrics
    forecast=list(forecast)
    for i in range(number_of_days):
            predicted_cost = forecast[i]
            previous_cost = forecast[i - 1] if i > 0 else None
            trend_color = ""
            if previous_cost is not None:
                if predicted_cost > previous_cost:
                    trend_color = "%"
                elif predicted_cost < previous_cost:
                    trend_color = "-%"
                else:
                    trend_color = "%"

                cols[i].metric(f"Predicted ( {day_names[i]} )",
                               f"{predicted_cost:.2f} (KWh)",
                               f"{trend_color}")
            else:
                cols[i].metric(f"Predicted ( {day_names[i]} )",
                               f"{predicted_cost:.2f} (KWh)",
                               f"{trend_color}")

    st.markdown('---')
    st.write("### Historical Data and Predictions ")
                # Display bar chart for historical data and predictions
    bar_chart_data = pd.DataFrame({'Date': forecast_index, 'Predicted Solar Gird Generation': forecast})

            # Plot bar chart
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=forecast_index, y=bar_chart_data['Predicted Solar Gird Generation'], name='Predicted Solar Gird Generation'))
    fig_bar.update_layout(xaxis_title='Date', yaxis_title='Total Solar Gird Generation (KWh)',
                                  title='Historical Data and Predictions for Next Days')
    st.plotly_chart(fig_bar,use_container_width=True)




# Set the title at the top of the Streamlit app
if hasattr(st.session_state, "logged_in") and st.session_state.logged_in:
    st.set_page_config(
    page_title="Energy Consumption Analytics",
    page_icon="Images/Lgo-Image-Eletric.png",  # You can use an emoji or provide a URL to an icon
    layout="wide",  # Set the layout to wide
    )
else:
    st.set_page_config(
        page_title="Hsieh",
        page_icon="Images/Lgo-Image-Eletric.png",  # You can use an emoji or provide a URL to an icon
    )

st.markdown("""
<script>
document.body.style.zoom = 0.8;
</script>
""", unsafe_allow_html=True)
st.markdown("""
<script>
document.body.style.zoom = 0.8;
</script>
""", unsafe_allow_html=True)

# App Navigation
def main():
    st.sidebar.image("Images/Lgo-Image-Eletric.png", caption="Energy Consumption Analytics", use_column_width=True)


    if hasattr(st.session_state, "logged_in") and st.session_state.logged_in:
        pages = {
            "Home": home,
            "Profile": profile,
            "Overall Consumption": overall_consumption,
            "House Hold Consumption": house_hold_consumption,
            "Solar Dicipation": solar_dacipation,
            "Interact with Data using AI":Interact_with_My_Data_using_AI,
            "Logout Account": logout,
        }
        st.sidebar.title("Energy Analytics")
        st.sidebar.markdown(f'Logged in as<span style="text-decoration:none; color:white ;">&nbsp;{st.session_state.user_good_name}</span>',unsafe_allow_html=True)
        st.sidebar.markdown("<br>", unsafe_allow_html=True)

    else:
        pages = {
            "Log In with Existing Account": Login,
            "Register Latest Account": Register,
            }
        st.sidebar.title("Accounts")

    selection = st.sidebar.selectbox("Select Page to Navigate", list(pages.keys()))
    page = pages[selection]
    page()

if __name__ == "__main__":
    main()