### Imports ###

# Standard Library imports
import os

# Google library imports for authentication to GCP and BigQuery
from google.oauth2 import service_account
from google.cloud import bigquery

# Functions to handle links, check tables of crawled pages and links in BigQuery, and retrieve URLs from sitemap.
from WebScraping.sitemapModification import getURLSFromSitemap
from WebScraping.alreadyCrawled import get_valid_crawled_pages, get_uncrawled_links
from WebScraping.universalResourceLinkHandler import is_valid_url

### End of Imports ###


### Function Definition ###


# Function generates a data dictionary comprising key parameters and data objects for web crawling.
# Encompasses credentials, database table details, URLs from a sitemap, and prior discovered links.
def get_data_dictionary(discoveredLinksTableName, # Table of stored links on prior crawl
                        keyFilePath, # Location of credentials to cloud
                        siteMapLocation, # Sitemap filepath to try to load additional URLs from
                        theProjectId, # GCP project ID to store data against
                        tableSet, # BigQuery table in GCP to store data in
                        websiteName, # Name of website to target
                        defaultDays=30): # Window to lookback in for data from past crawls

    """
    Generate a data dictionary for web crawling with the specified parameters.

    Parameters:
    - discoveredLinksTableName (str): Table of stored links from a prior crawl.
    - keyFilePath (str): Location of credentials JSON file for cloud access.
    - siteMapLocation (str): Filepath of the sitemap to load additional URLs from.
    - theProjectId (str): GCP project ID to store data against.
    - tableSet (str): BigQuery table in GCP to store data in.
    - websiteName (str): Name of the target website.
    - defaultDays (int): Number of historic days to consider in the database, if records exist in time window.

    Returns:
    dict: A dictionary containing the following keys:
        - 'mainPayloadArguments': List of main payload arguments for cloud data upload.
        - 'completedURLs': List of completed URLs stored in the specified BigQuery table.
        - 'additionalURLs': List of additional URLs obtained from the sitemap and discovered links.
        - 'linkUploadArguments': List of arguments for uploading discovered links to a separate table.
    """

    # Load credentials from the JSON key file
    credentials = service_account.Credentials.from_service_account_file(keyFilePath)

    # Define mainPayloadArguments for uploading data to the cloud now that we have our credentials
    mainPayloadArguments = [credentials,
                            theProjectId,
                            tableSet,
                            websiteName,
                            ['Page', 'Page Text', 'Response Log', 'Crawl Experience', 'Date', 'Time']
                            ]

    # Client object to communicate to BigQuery
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    # Target table storing completed URLs
    completedURLs = get_valid_crawled_pages(client,
                                            theProjectId,
                                            tableSet,
                                            websiteName,
                                            'Page',
                                            'Page Text',
                                            'Date',
                                            defaultDays,
                                            )

    # Get URLs from a sitemap, if passed.
    if len(siteMapLocation) is not None:
        try:
            additionalURLs = list(set(getURLSFromSitemap(siteMapLocation)))
        # Warn if we could not get the sitemap for some reason and print the corresponding error
        except Exception as e:
            print('Tried to get sitemap, but failed!')
            print(str(e))
            additionalURLs = []
    else:
        additionalURLs = []

    # Tries to get URLs from a previous crawl, if we discovered links, but did not then crawl them
    try:
        evenMoreURLs = get_uncrawled_links(client,
                                           theProjectId,
                                           tableSet,
                                           discoveredLinksTableName,
                                           'Link',
                                           'Date')
    except:
        evenMoreURLs = []

    # Combine URLs we have discovered but haven't crawled in the sitemap.
    additionalURLs = additionalURLs + evenMoreURLs
    additionalURLs = list(set(additionalURLs))

    # Filter any URLs crawled with ? and # parameters we don't want
    additionalURLs = [x.split('?')[0] for x in additionalURLs]
    additionalURLs = [x.split('#')[0] for x in additionalURLs]
    # Delete copies after reduced URLs to base form
    additionalURLs = list(set(additionalURLs))

    # Ensure remaining URLs are valid
    additionalURLs = [x for x in additionalURLs if is_valid_url(x) is True]

    # Reference table to hold links we discover while crawling for next crawl.
    linkUploadArguments = [credentials, theProjectId, tableSet, discoveredLinksTableName, ['Date', 'Time', 'Link']]

    # Create and return the dictionary
    data_dictionary = {
        'mainPayloadArguments' : mainPayloadArguments,
        'completedURLs': completedURLs,
        'additionalURLs': additionalURLs,
        'linkUploadArguments': linkUploadArguments
    }

    return data_dictionary

### End of Function Definition ###