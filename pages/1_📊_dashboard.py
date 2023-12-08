import streamlit as st
import os
import requests
import boto3
import time
import datetime
import pandas as pd

# Query range
start_date = "01/12/2023"
my_time = time.strptime(start_date, "%d/%m/%Y")
start_date_timestamp = int(time.mktime(my_time))
today_date_timestamp = int(time.time())

# Table info
IOT_TABLE_NAME = "iot_data_ddb"
PARTITION_KEY = 'sample_time'

@st.cache_data
def load_iot_table():
    # DynamoDB Connection
    dynamo_client  =  boto3.resource(
        service_name = 'dynamodb',
        region_name = 'us-east-2',
        aws_access_key_id = st.session_state['aws_access_key_id'],
        aws_secret_access_key = st.session_state['aws_secret_access_key']
    )
    iot_table = dynamo_client.Table(IOT_TABLE_NAME)

    # Query - It is not the most performatic way. Re-evaluate to use "query" statement
    response = iot_table.scan(
        FilterExpression=Key(PARTITION_KEY).between(start_date_timestamp, today_date_timestamp)
        #FilterExpression=Key(PARTITION_KEY).between(1701966506162, 1701966531596)
    )

    # Convert into DataFrame
    iot_df = pd.DataFrame(response['Items'])
    iot_df['temperature'] = iot_df['device_data'].map(lambda d : d['temperature'])
    iot_df['light'] = iot_df['device_data'].map(lambda d : d['light'])
    iot_df = iot_df.drop(columns=["device_data"])

    return (iot_df)

iot_df = load_iot_table()
st.write(iot_df)