import streamlit as st
import os
import requests
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from decimal import *
import time
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Read AWS Credentials from Environment Variable
if "aws_access_key_id" not in st.session_state:
    st.session_state['aws_access_key_id'] = os.environ['AWS_ACCESS_KEY_ID']
if "aws_secret_access_key" not in st.session_state:
    st.session_state['aws_secret_access_key'] = os.environ['AWS_SECRET_ACCESS_KEY']

# Query range
start_date = "01/01/2023"
my_time = time.strptime(start_date, "%d/%m/%Y")
start_date_timestamp = int(time.mktime(my_time)) * 1000
today_date_timestamp = int(time.time()) * 1000

# Table info
IOT_TABLE_NAME = "iot_data_ddb"
TEMP_ALARMS_TABLE_NAME = "temperature_alarms"

PARTITION_KEY = 'sample_time'

#@st.cache_data
def load_iot_table():
    # DynamoDB Connection

    dynamo_client  =  boto3.resource(
        service_name = 'dynamodb',
        region_name = 'us-east-2',
        aws_access_key_id = st.session_state['aws_access_key_id'],
        aws_secret_access_key = st.session_state['aws_secret_access_key']
    )
    try:
        iot_table = dynamo_client.Table(IOT_TABLE_NAME)
        temp_alarms_table = dynamo_client.Table(TEMP_ALARMS_TABLE_NAME)
    except ClientError as e:
        return (pd.DataFrame(),pd.DataFrame(),pd.DataFrame())
    
    # Query - It is not the most performatic way. Re-evaluate to use "query" statement
    try:
        response = iot_table.scan(
            FilterExpression=Key(PARTITION_KEY).between(start_date_timestamp, today_date_timestamp)
        )
    except ClientError as e:
        return (pd.DataFrame(),pd.DataFrame(),pd.DataFrame())

    try:
        temp_alarms = temp_alarms_table.scan(
            FilterExpression=Key(PARTITION_KEY).between(start_date_timestamp, today_date_timestamp)
        )
    except ClientError as e:
        return (pd.DataFrame(),pd.DataFrame(),pd.DataFrame())
    
    # Convert into DataFrame
    iot_df = pd.DataFrame(response['Items'])
    temp_alarms_df = pd.DataFrame(temp_alarms['Items'])
    
    # Temperature DF
    temp_df = iot_df[iot_df['device_data'].astype(str).str.contains("temperature")==True].copy()
    temp_df['temperature'] = temp_df['device_data'].map(lambda d : d['temperature'])
    temp_df['device'] = temp_df['device_data'].map(lambda d : d['device'] if "device" in d else "avr")
    temp_df = temp_df.drop(columns=['device_data'])
    temp_df['sample_time'] = temp_df['sample_time'].astype(np.int64)
    temp_df['sample_time'] = pd.to_datetime(temp_df['sample_time'],unit="ms")
    temp_df = temp_df.sort_values("sample_time",ascending=True)
    
    light_df = iot_df[iot_df['device_data'].astype(str).str.contains("light")==True].copy()
    light_df['light'] = light_df['device_data'].map(lambda d : d['light'])
    light_df['device'] = light_df['device_data'].map(lambda d : d['device'] if "device" in d else "avr")
    light_df = light_df.drop(columns=['device_data'])
    light_df['sample_time'] = light_df['sample_time'].astype(np.int64)
    light_df['sample_time'] = pd.to_datetime(light_df['sample_time'],unit="ms")
    light_df = light_df.sort_values("sample_time",ascending=True)

    return (temp_df,light_df, temp_alarms_df)

temp_df,light_df, temp_alarms_df = load_iot_table()
if len(temp_df) == 0 or len(light_df) == 0 :
    st.write ("Please verify the AWS Credentials.")
    exit()
    
# Presentation
temp_col, light_col = st.columns(2,gap="small")
temp_alarms_col = st.container()

# Temperature
#fig_temp = px.line(
#    iot_df,
#    x='sample_time',
#    y="temperature",
#    title="Temperatura"
#)
# Create figure
fig_temp = go.Figure()
temp_df = temp_df[['sample_time','temperature','device']]
temp_avr_df = temp_df.loc[temp_df['device'] == "avr"][['sample_time','temperature']]
temp_esp_df = temp_df.loc[temp_df['device'] == "esp32"][['sample_time','temperature']]
temp_py_df = temp_df.loc[temp_df['device'] == "py"][['sample_time','temperature']]

temp_avr_df.set_index("sample_time",inplace=True)
temp_avr_df = temp_avr_df.resample('1min').mean()
temp_esp_df.set_index("sample_time",inplace=True)
temp_esp_df = temp_esp_df.resample('1min').mean()
temp_py_df.set_index("sample_time",inplace=True)
temp_py_df = temp_py_df.resample('1min').mean()


fig_temp.add_trace(
    go.Scatter(
        x=list(temp_avr_df.index), 
        y=list(temp_avr_df['temperature']),
        mode='lines',
        name='avr'
    )
)

fig_temp.add_trace(
    go.Scatter(
        x=list(temp_esp_df.index), 
        y=list(temp_esp_df['temperature']),
        mode='lines',
        name='esp32'
    )
)

fig_temp.add_trace(
    go.Scatter(
        x=list(temp_py_df.index), 
        y=list(temp_py_df['temperature']),
        mode='lines',
        name='py'
    )
)

# Add range slider
fig_temp.update_layout(
    title="Variação de Temperatura",
    xaxis_title="Tempo",
    yaxis_title="Temperatura (C)",
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1h",
                     step="hour",
                     stepmode="backward"),
                dict(count=1,
                     label="1d",
                     step="day",
                     stepmode="backward"),
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    )
)

temp_col.plotly_chart(fig_temp,use_container_width=True)

# Light
#fig_light = px.line(
#    light_df,
#    x='sample_time',
#    y="light",
#    color="device",
#    title="Variação de Luminosidade",
#    labels={
#       "sample_time": "Tempo",
#       "light": "Luminosidade"
#   }
#)

# Light - Create figure
fig_light = go.Figure()
light_df = light_df[['sample_time','light','device']]
light_avr_df = light_df.loc[light_df['device'] == "avr"][['sample_time','light']]
#light_esp_df = light_df.loc[light_df['device'] == "esp32"][['sample_time','light']]
light_py_df = light_df.loc[light_df['device'] == "py"][['sample_time','light']]


light_avr_df.set_index("sample_time",inplace=True)
light_avr_df = light_avr_df.resample('1min').mean()
#light_esp_df.set_index("sample_time",inplace=True)
#light_esp_df = light_esp_df.resample('1min').mean()
light_py_df.set_index("sample_time",inplace=True)
light_py_df = light_py_df.resample('1min').mean()

fig_light.add_trace(
    go.Scatter(
        x=list(light_avr_df.index), 
        y=list(light_avr_df['light']),
        mode='lines',
        name='avr'
    )
)

fig_light.add_trace(
    go.Scatter(
        x=list(light_py_df.index), 
        y=list(light_py_df['light']),
        mode='lines',
        name='py'
    )
)


# Add range slider
fig_light.update_layout(
    title="Variação de Luminosidade",
    xaxis_title="Tempo",
    yaxis_title="Luminosidade (Lumens)",
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1h",
                     step="hour",
                     stepmode="backward"),
                dict(count=1,
                     label="1d",
                     step="day",
                     stepmode="backward"),
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    )
)
light_col.plotly_chart(fig_light,use_container_width=True)

# Temperature Alarms
fig_temp_alarms = go.Figure()
temp_alarms_df.set_index("sample_time",inplace=True)

fig_temp_alarms.add_trace(
    go.Scatter(
        x=list(temp_alarms_df.index), 
        y=list(temp_alarms_df['average_temperature']),
        marker_size=5,
        marker_color=['#F55030' for i in range(0,len(temp_alarms_df)) ],
        mode='markers',
        text=temp_alarms_df['temperature_threshold']
    )
)

# Add range slider
fig_temp_alarms.update_layout(
    title="Alarmes de Temperatura Média no Último Minuto",
    xaxis_title="Tempo",
    yaxis_title="Temperatura Média (Celsius)",
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1h",
                     step="hour",
                     stepmode="backward"),
                dict(count=1,
                     label="1d",
                     step="day",
                     stepmode="backward"),
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    )
)
temp_alarms_col.plotly_chart(fig_temp_alarms,use_container_width=True)
