from typing import Union, List

from fastapi import FastAPI
from pytrends.request import TrendReq
import pandas as pd
from datetime import date
import datetime as dt
from datetime import datetime, timedelta

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/market_growth")
def market_growth(keywords_list: List[str]):
    pytrends = TrendReq(hl='en-US', tz=360)
    # Build payload
    # we can only have upto 5 terms in the list
    # if geo is not specified then it is considered by default world
    pytrends.build_payload(kw_list=keywords_list, timeframe='today 5-y')
    # Retrieve interest over time data
    interest_over_time_df = pytrends.interest_over_time()
    interest_over_time_df.drop(columns=['isPartial'], inplace=True)
    interest_over_time_df['mean'] = interest_over_time_df.mean(axis=1)
    # print(interest_over_time_df)

    # Calculate the year-wise mean for the 'Value' column
    yearly_mean = interest_over_time_df.groupby(interest_over_time_df.index.year)['mean'].mean()

    # round off the values to two decimal places
    yearly_mean = yearly_mean.round(2)

    data = []
    for year, value in yearly_mean.items():
        data.append({'year': year, 'trend': value})

    new_dic = {'market_growth': data}
    return new_dic


@app.post("/division_of_market_share")
def division_of_market_share(keywords_list: List[str]):
    return {
        "monopoly": 75,
        "competitive": 25

    }


@app.post("/geographic_distribution")
def geographic_distribution(keywords_list: List[str]):
    # Get today's date
    today = datetime.now().date()

    # Calculate 4 days before today
    four_days_before = today - timedelta(days=4)

    # Calculate 5 days before today
    five_days_before = today - timedelta(days=5)

    # Format the dates as YYYY-MM-DD
    formatted_four_days_before = four_days_before.strftime('%Y-%m-%d')
    formatted_five_days_before = five_days_before.strftime('%Y-%m-%d')
    dataframes = []

    # this is for four days before date
    for term in keywords_list:
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload(kw_list=[term],
                               timeframe=formatted_four_days_before + ' ' + formatted_four_days_before)
        # Retrieve interest by region data
        interest_by_region_df = pytrends.interest_by_region(resolution='COUNTRY')
        # print(interest_by_region_df)
        dataframes.append(interest_by_region_df[term])

    # Merge the DataFrames into a single DataFrame
    merged_df1 = pd.concat(dataframes, axis=1)

    # print(merged_df1)
    merged_df1['average'] = merged_df1.mean(axis=1)
    top_countries_4_days_ago = merged_df1.sort_values(by='average', ascending=False).head(20)
    # print(top_countries_4_days_ago)

    # this is for five days before data
    dataframes = []
    for term in keywords_list:
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload(kw_list=[term],
                               timeframe=formatted_five_days_before + ' ' + formatted_five_days_before)
        # Retrieve interest by region data
        interest_by_region_df = pytrends.interest_by_region(resolution='COUNTRY')
        # print(interest_by_region_df)
        dataframes.append(interest_by_region_df[term])

    # Merge the DataFrames into a single DataFrame
    merged_df2 = pd.concat(dataframes, axis=1)

    # print(merged_df2)
    merged_df2['average'] = merged_df2.mean(axis=1)
    top_countries_5_days_ago = merged_df2.sort_values(by='average', ascending=False).head(20)
    # print(top_countries)

    # calculating the percentage change
    # Calculate percentage change for each top region from four days ago using five days ago data
    percentage_changes = []
    for index, row in top_countries_4_days_ago.iterrows():
        region_name = index
        if region_name in merged_df2.index:
            print(str(row['average']) + "," + str(merged_df2.loc[region_name, 'average']))
            percentage_change = ((row['average'] - merged_df2.loc[region_name, 'average']) / merged_df2.loc[
                region_name, 'average']) * 100
            if percentage_change == float('inf'):
                percentage_change = 100  # Set to 100% if the calculation results in infinity
            percentage_changes.append(percentage_change)
        else:
            print("hi")
            percentage_changes.append(None)

    # Round off each value in the percentage_changes list to two decimal places
    rounded_percentage_changes = [round(value, 2) for value in percentage_changes]

    # Add the percentage change column to the top_countries_4_days_ago dataframe
    top_countries_4_days_ago['percentage_change'] = rounded_percentage_changes

    top_countries_list = []
    for index, row in top_countries_4_days_ago.iterrows():
        region_dict = {
            'geoName': index,
            'average': row['average'],
            'percentage_change': row['percentage_change']
        }
        top_countries_list.append(region_dict)

    print(top_countries_list)
    return {'top_countries_list': top_countries_list}
