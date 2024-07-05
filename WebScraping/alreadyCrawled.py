# 
import datetime as dt
import pandas as pd

#
from google.api_core.exceptions import NotFound

# Import URL link handler from within this project
from WebScraping.universalResourceLinkHandler import truncateURLListToBaseForm


# Get URLs we need to crawl that we discovered from prior page crawls. Connects to BigQuery
def get_uncrawled_links(client,
                       project_name,
                       dataset_name,
                       table_name,
                       target_column,
                       date_column,
                       n_days=30,
                       *args):

    # Attempt to get links discovered on prior crawls within the last n_days that are not yet crawled.
    try:
        # Build query to retrieve latest valid crawl for each distinct entry in target column
        query = f"SELECT {target_column} FROM `{project_name}.{dataset_name}.{table_name}` " \
                f"WHERE DATE({date_column}) >= DATE_SUB(CURRENT_DATE(), INTERVAL {n_days} DAY)"
        print(query)

        # Get dataframe, using the dynamically built query
        df = client.query(query).to_dataframe()

        # Return the list of Links to crawl
        resultList = df[target_column].tolist()
    except NotFound as nfe:
        print(str(nfe))
        resultList = []

    return resultList


def get_valid_crawled_pages(client,
                            project_name,
                            dataset_name,
                            table_name,
                            target_column,
                            filter_column,
                            date_column,
                            n_days=30,
                            end_date=None,
                            *args):

    # Get current time in UTC
    now_utc = dt.datetime.utcnow()

    # Calculate start time based on specified number of days
    start_time = now_utc - dt.timedelta(days=n_days)

    # If end_date is not specified, use current time
    if end_date is None:
        end_date = now_utc

    # Attempt to call a table in BigQuery with URLs previously crawled.
    try:
        # Build query to retrieve latest valid crawl for each distinct entry in target column
        query = f"SELECT {target_column}, " \
                f"{filter_column}, " \
                f"{date_column}, " \
                f"FROM `" \
                f"{project_name}.{dataset_name}.{table_name}`"

        # Get dataframe, using the dynamically built query
        df = client.query(query).to_dataframe()

        # Return a list of URLs, truncated to before the ?, that were retrieved within the last n_days
        initialValidCrawlURLs = filterToValidCrawls(df, date_column, 'Text', target_column, start_time, end_date)
        validCrawlURLs = truncateURLListToBaseForm(initialValidCrawlURLs)
    # If we failed to locate a valid table of prior crawled URLs, return an empty list
    except NotFound as nfe:
        print(str(nfe))
        validCrawlURLs = []


    return validCrawlURLs



# Gets the most up to date data for a table where the target column has an entry
def filterToValidCrawls(df, date_column, filter_column, target_column, start_time, end_date):

    # Convert date_column to datetime if it is not already datetime
    if not isinstance(df[date_column].dtype, pd.DatetimeTZDtype):
        df[date_column] = pd.to_datetime(df[date_column])

    # Filter dataframe based on the date column
    df = df[(df[date_column] >= start_time) & (df[date_column] <= end_date)]

    # Remove rows where the target column is empty
    df = df[df[filter_column].notnull()]

    # Sort dataframe by date column in descending order
    df = df.sort_values(date_column, ascending=False)

    # Group dataframe by target column and keep the first row for each group
    df = df.groupby(target_column).first()

    # Get the values of the target column as a list and return
    df = df.reset_index()
    resultList = df[target_column].tolist()
    print('\n')
    print('Converted target column to list')
    print(len((resultList)))

    return resultList

## Target table storing completed URLs
#completedURLs = get_valid_crawled_pages(client,
#                                        'yourProject',
#                                        'yourTableSet',
#                                        'yourTable',
#                                        'Page',
#                                        'Page Text',
#                                        'Date',
#                                       )