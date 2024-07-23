### IMPORTS ###

# Standard Python Library.
import datetime as dt
import os
import pandas as pd
import threading

# Imports from metabeaver. Beaver on.
from metabeaver.OperationBeaver.logCollector.defaultLogger import Logger

# Scripts from other directories.
from CloudFunctions.Google.bigQueryInputOutput import append_to_bigquery_table, append_set_to_bigquery_table
from WebScraping.defaultSeleniumSettings import initiateDriver

# Scripts within this directory
from WebScraping.cloudAuthenticator import get_data_dictionary
from WebScraping.justTheScraper import crawl_website
from WebScraping.threadedManagement import check_driver_status

### END OF IMPORTS ###


### Function Definition ###



### End of Function Definition ###


### FROZEN VARIABLES ###



### END OF FROZEN VARIABLES ###


### DYNAMIC LOGIC ###

# Create Logger object that will be utilised throughout the debugging of the crawl process
logger = Logger()

# Date for today to use in crawl logic
currentDate = pd.to_datetime('today').strftime('%Y-%m-%d')
# Time for today to use in crawl logic
start_time = dt.datetime.now()

## Retrieve details about the webscrape from running host environment
# Account credentials for GCP uploads.
keyFilePath = os.environ['keyFileLocation']
# target website. Full valid home page URL
fullWebName = os.environ['fullAddress'] # e.g. https://www.orchardnetwork.org.uk/about
# Target website. Short name for referring to.
websiteNickname = os.environ['crawlDomain'] # e.g. orchard_network_uk
# Sitemap Location. Syntactic sugar.
siteMapLocation = os.environ['siteMapLocation']
# Define endpoint in the cloud and send to helper upload function
theProjectId = os.environ['projectId']
# Get GCP tableSetId. Future update this to func/cloud specific args.
tableSet = os.environ['tableSetId']
# Create table name that is the target for discovered but uncrawled links
discoveredLinksTableName = websiteNickname + '_tocrawl'
logger.log('Retrieved critical variables from environment.')

# Using the values we defined, retrieve a data dictionary for crawled URLs, discovered URLs, link and payload arguments.
dataDictionary = get_data_dictionary(
    discoveredLinksTableName,
    siteMapLocation,
    theProjectId,
    tableSet,
    websiteNickname,
    defaultDays=10,
)
logger.log('Retrieved critical link data structure to define crawl links.')

# Access elements of the dictionary directly just for readability purposes
additionalURLs = dataDictionary.get('additionalURLs')
allCompletedURLs = dataDictionary.get('completedURLs')
linkUploadArguments = dataDictionary.get('linkUploadArguments')
mainPayloadArguments = dataDictionary.get('mainPayloadArguments')

# Loads a selenium driver which we will use to crawl the website defined in the metadata
logger.log('Instantiating driver...')
driver = initiateDriver()
logger.log('Instantiated driver!')

# Start the check_driver_status thread
driver_status_thread = threading.Thread(target=check_driver_status,
                                        args=(start_time, driver)
                                        )
driver_status_thread.start()
logger.log('Initiated monitoring thread')

# Crawl the website.
# Starts at homepage, or first page in uncrawled list.
crawl_website(driver, # Selenium driver we will use in a crawl.
              fullWebName, # Website homepage to start a crawl with.
              additionalURLs, # Any additional URLs to crawl. From a sitemap, or uncrawled links previously harvested.
              allCompletedURLs, # All URLs completed within the last n days, where n is a user specified number (int).
              3, # Number of times to recursively try to crawl a given page.
              append_to_bigquery_table, # Upload to database function. Uploads crawled page data.
              mainPayloadArguments, # Arguments for our function that uploads crawled page data.
              append_set_to_bigquery_table, # Upload to database function. Uploads links.
              linkUploadArguments, # Arguments for our function that uploads page links
              patternList=['.*'], # Crawls all URLS. Use site specific regex, e.g: ['.*\/en\/us\/.*', '.*\/en\/uk\/.*']
)
logger.log(f'Crawling website, {websiteNickname}')

### END OF DYNAMIC LOGIC ###