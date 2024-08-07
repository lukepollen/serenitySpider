# If Chrome is run without a head...
# ... The following verse need not be read.
#
# If you wish the crawler to work and not to weep,
# Make sure your machine is not set to sleep.
# Go to power settings and look for advanced,
# Change a few knobs for this crawler to dance;
# Never to turn off screen or sleep when on power,
# And we'll scrape the web, hour by hour.


### IMPORTS ###

# Imports from Python Standard Library
import datetime as dt
import os
import re
import subprocess
import sys
from urllib.parse import urljoin, urlparse

# Imports from Python extended ecosystem
import pandas as pd

from bs4 import BeautifulSoup
from metabeaver.Formatting.printControl import conditional_print as cprint
from metabeaver.OperationBeaver.logCollector.defaultLogger import Logger
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Imports from within project
from WebScraping.universalResourceLinkHandler import is_valid_url, getUrlDepth

### END Of IMPORTS ###


### Class Definition ###

class LinkBank:

    # Initialise the class with the link upload function, the arguments for the function, link num to retain, time/date.
    def __init__(self, linkUploadFunc, linkUploadArgs, bank_limit=256):

        self.bank_limit = bank_limit
        self.link_bank = set()
        self.linkUploadFunc = linkUploadFunc
        self.linkUploadArgs = linkUploadArgs

        # Get today's date as a string to add to the links to crawl
        self.todayDate = dt.datetime.today().strftime('%Y-%m-%d')
        # Get today's time as a string to add to the links to crawl
        self.todayTime = dt.datetime.today().strftime('%H:%M:%S')

        # Set a reference to application wide logger
        self.logger = Logger()

    # Add a link to the set to store.
    def add_link(self, link):

        # Parse the domain from the given link
        parsed_link_domain = urlparse(link).netloc
        self.logger.log(f'Parsed link domain: {parsed_link_domain}')

        # Parse the domain from the fullAddress environment variable
        current_domain = urlparse(os.environ['fullAddress']).netloc
        self.logger.log(f'Parsed current domain: {current_domain}')

        # Check if the parsed domain matches the current domain
        if parsed_link_domain == current_domain:
            self.link_bank.add(link)

        self.link_bank.add(link)
        if len(self.link_bank) >= self.bank_limit:
            self.upload_to_cloud()

    # Using the function and the arguments that we provided, upload the links to the cloud
    def upload_to_cloud(self):
        # Upload the links and perform a reset to an empty set for storing next links
        if not self.link_bank:
            return

        # Upload a dataframe of links to the cloud.
        self.logger.log(f"Uploading {len(self.link_bank)} links to the cloud.")
        # Convert link bank to DataFrame
        fullLinkData = [[self.todayDate, self.todayTime, x] for x in self.link_bank]
        df = pd.DataFrame(fullLinkData, columns=['Date', 'Time', 'Link'])
        self.logger.log('Created dataframe of links in form of [theDate, theTime, theLink]')

        # Use the provided upload function and arguments
        self.linkUploadFunc(self.linkUploadArgs, df)
        self.logger.log('Uploaded dataframe of links!')

        # Expand length of link bank in powers of two; retain memory of encountered links, but slowly increase memory.
        self.bank_limit = self.bank_limit + 256
        self.logger.log(f'Increased storage capacity to {str(self.bank_limit)}')

    def upload_remaining_links(self):
        self.upload_to_cloud()


### End of Class Definition ###


### FUNCTION DEFINITION ###

def apply_upload(uploadFunc, uploadArgs, pageCrawlData):

    uploadFunc(uploadArgs, pageCrawlData)

# Crawl a list of pages, and generate a dictionary like {page : [bodyText, responseLog]}
def crawlPage(driver, eachPage, count, uploadFunc, uploadArgs):

    # Instantiate the Logger for recording and debugging.
    logger = Logger()

    # Get the element we want to crawl from environment vars
    extractElement = os.environ.get('extractElement', 'body')

    # Get the date and the time when this function was called
    now = dt.datetime.now()

    # Extract date and time as separate variables, convert both to strings
    date = str(now.date())
    time = str(now.time()).replace(':', '').replace('.', '')

    # Set success conditions to False and update on each milestone. Printed in verbose mode.
    truthDictionary = {
    'wasFullLoaded' : False,
    'gotBodyText' : False,
    'gotResponseLog' : False,
    'gotWebCode' : False,
    'successfulComplete' : False,
    }

    # Set a dummy variables for the page_text we wish to retrieve
    page_text = ''

    # Crawl data: url, url page text, network response log, dictionary of boolean values of crawl states, day, time
    pageCrawlData = [eachPage, '', '', truthDictionary, date, time]

    ## Get the page in selenium. Warn if crawl fails. Warn on exceptions at each stage.
    # Waits until the page load is complete, up to 60s, to try to locate the body of the HTML document.
    try:
        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, extractElement)))
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        truthDictionary['wasFullLoaded'] = True
        logger.log('Got a fully loaded page:')
        logger.log(eachPage)
    # Warn user where we did  not get a document.readyState == complete and / or location of <body> failed
    except Exception as e:
        logger.log(eachPage)
        logger.log('Wait for page load failed')
        logger.log(f'While waiting for page load, got a generic Exception waiting for the page: {str(e)}')

        count = count - 1

        # Try to recursively crawl the page if failed attempts not equal to count
        if count > 0:
            crawlPage(driver, eachPage, count, uploadFunc, uploadArgs)
        else:
            pageCrawlData = [eachPage,
                             'Failed to crawl page due to Page Load Timeout',
                             'No network response',
                             truthDictionary,
                             date,
                             time]

    # Get the body text.
    try:
        # Get the page in the Chrome instance.
        driver.get(eachPage)
        # Get the raw HTML content of the page.
        raw_html = driver.page_source

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(raw_html, 'html.parser')
        # Extract either all visible text or the raw HTML.
        if os.environ.get('parse_type', 'html') == 'text':
            page_text = soup.get_text(separator='\n', strip=True)
        else:
            # Cast raw HTML to string because JSON makes data engineers sad.
            page_text = str(soup)

        # Update the crawl data with the page text we've parsed from the raw HTML.
        pageCrawlData[1] = page_text
        truthDictionary['gotBodyText'] = True
        logger.log('Got pageText.')
    # Try to recursively crawl a page on a timeout of retrieving body text
    except (TimeoutException, WebDriverException) as e:

        # Warn on failed attempt to driver.get() a page due to timeout
        logger.log(eachPage)
        logger.log('Hit a TimeoutException or WebDriverException!')
        logger.log(f'While retrieving loaded page data, got an TimeoutException or WebDriverException: {str(e)}')
        count = count - 1

        # Try to recursively crawl the page if failed attempts not equal to count
        if count > 0:
            crawlPage(driver, eachPage, count, uploadFunc, uploadArgs)
        else:
            pageCrawlData = [eachPage,
                             'Failed to crawl page due to Timeout Exception',
                             'No network response',
                             truthDictionary,
                             date,
                             time]
    # Set body text for page to error message if page was crawled OK, but could not get text from it.
    except Exception as e:

        # If there was an exception of any other kind to Timeouts, alert the user and print error warning
        logger.log(eachPage)
        logger.log(f'While retrieving loaded page data, got a generic Exception: {str(e)}')

        # Attempt a recursive crawl
        if count > 0:
            count = count - 1
            crawlPage(driver, eachPage, count, uploadFunc, uploadArgs)
        else:
            pageCrawlData = [eachPage,
                             'Failed to crawl page due to Exceptions',
                             'No network response',
                             truthDictionary,
                             date,
                             time]


    # Get the response log. Extract the HTTP code, and store the full log.
    try:
        #responseLog = driver.get_log('performance')
        responseLog = ''
        pageCrawlData[2] = responseLog
        truthDictionary['gotResponseLog'] = True
        logger.log('Got the response log.')
    # Use default warning value on failed response log retrieval steps
    except Exception as e:

        logger.log(eachPage)
        logger.log('Could not retrieve the response log!')

        # Store error value for the response log if we could not retrieve network values
        pageCrawlData[2] = 'Could not retrieve the response log!'
        logger.log(f'While trying to retrieve driver log, got a generic Exception: {str(e)}')
        logger.log('Could not retrieve the response log!')

    # If we got a fully loaded page, text from the body, with a network log and HTTP code, consider crawl a success.
    if (truthDictionary.get('wasFullLoaded') == True and
            truthDictionary.get('gotBodyText') == True and
            truthDictionary.get('gotResponseLog') == True and
            truthDictionary.get('gotWebCode') == True):
        truthDictionary['successfulComplete'] = True

    # Replace line break symbol with an actual gap in the text.
    if os.environ.get('parse_type', 'html') == 'text':
        try:
            page_text = page_text.replace("\n", " ")
            pageCrawlData[1] = page_text
        except TypeError as te:
            logger.log(f'While trying to replace newlines, got a NoneType Error: {str(te)}')
            pageCrawlData[1] = ''
        except UnboundLocalError as ule:
            logger.log(f'While trying to replace newlines, got an UnboundLocalError:  {str(ule)}')
            pageCrawlData[1] = ''

    # Print the progress if we asked metabeaver.formatting.conditionalPrint to be talkative
    logger.log('\n')
    logger.log('The page was: ' + eachPage)

    # Conditionally print the status of the call, if we have a talkative beaver.
    logger.log('\n')
    for k, v in truthDictionary.items():
        logger.log('Printing page crawl milestones')
        logger.log(k + ' : ' + str(v))

    # Create a string that gives the truth values for each stage of potential success
    pageCrawlData[3] = ', '.join([f"{key}: {value}" for key, value in truthDictionary.items()])

    # Send the crawled data to the cloud
    logger.log('Attempting cloud upload...')
    apply_upload(uploadFunc, uploadArgs, pageCrawlData)
    logger.log('Cloud upload successful!')

    # Return the driver, in case we are crawling from the homepage, or wish to perform other actions on loaded page
    return driver


# Crawl a website by starting from the home page
def crawl_website(driver,
                  start_page,
                  additionalPages,
                  filterPages,
                  count,
                  maxURLs,
                  uploadFunc,
                  uploadArgs,
                  linkUploadFunc,
                  linkUploadArgs,
                  maxDepth=3,
                  patternList=['.*'],
                  ):

    # Execute the entire crawl within a try-finally block: we raise a sys.exit(0) on either complete or except
    try:
        # Reference the application-wide Logger class
        logger = Logger()

        # Create a LinkBank to store crawled link for progressive link uploads to the cloud
        linkBank = LinkBank(linkUploadFunc, linkUploadArgs)

        # Alert the user to the page we will start with
        logger.log('Start page is: ' + start_page)

        # Set to hold crawled pages
        crawled_pages = list(set(filterPages))

        # Set to hold pages to be crawled. Add home page to additional page.
        pages_to_crawl = set([start_page] + additionalPages)
        # Convert back to list
        pages_to_crawl = list(pages_to_crawl)

        # Remove any non-desired pages that matched filterPages
        pages_to_crawl = [page for page in pages_to_crawl if page not in crawled_pages]

        # Sanitise the URLs, so we only consider base URL structures occurring before ? parameter
        for i, page in enumerate(pages_to_crawl):
            if '?' in page:
                pages_to_crawl[i] = page.split('?')[0]

        # Convert the pages to crawl to a set and alert total pages we need to crawl
        pages_to_crawl = set(pages_to_crawl)
        logger.log('Total pages to crawl is: ' + str(len(pages_to_crawl)))

        # Base domain to reference when examining links
        domain = urlparse(start_page).netloc

        # While we have discovered pages we have not yet crawled, continue crawling
        urlsCrawled = 0
        while pages_to_crawl and urlsCrawled < maxURLs:

                # Get the next page to crawl
                page = pages_to_crawl.pop()

                # Check if the page has already been crawled and is within crawler seek depth limit
                if (page not in crawled_pages) and (getUrlDepth(start_page, page) <= int(maxDepth)):

                    logger.log(f'Going to crawl page: {page}')
                    # Crawl the page
                    driver = crawlPage(driver, page, count, uploadFunc, uploadArgs)
                    # Add the page to the set of crawled pages
                    crawled_pages.append(page)
                    urlsCrawled = urlsCrawled + 1
                    logger.log(f'Crawler budget remaining: {maxURLs - urlsCrawled}')

                    # Extract links from the page
                    new_links = extract_links(driver, page)

                    # Only add new links to crawl which are same domain
                    for link in new_links:
                        # Do not add link if we've already crawled.
                        if link not in crawled_pages:
                            logger.log('Adding link, ' + str(link))
                            # Do not add link to crawl if matches external, email, or antipattern
                            if not is_external_url(link, domain):
                                if not is_email_link(link):
                                    # Include link only if matches one or more inclusion pattern. Crawl with .* for all pages.
                                    if any(re.match(pattern, link) for pattern in patternList):

                                        # Ignore appendages after ? character and only crawl base URL structure.
                                        if '?' in link:
                                            link = link.split('?')[0]

                                        # Ignore appendages after # character and only crawl base URL structure.
                                        if '#' in link:
                                            link = link.split('#')[0]

                                        # After all checks and modifications, check we still have a valid URL. Ignore if bad.
                                        stillValidLink = is_valid_url(link)
                                        logger.log('Got a valid link to append!')

                                        # Continue to the next link to check if we did not get a valid link on this iteration.
                                        if not stillValidLink:
                                            continue

                                        # Add link to crawl location
                                        pages_to_crawl.add(link)

                                        # Add link to link bank to remember / upload when we hit target amount
                                        linkBank.add_link(link)
                                        logger.log('Added link to bank.')

        ## Finalise the crawl by logging total pages crawled and uploading remaining links
        # Print the total number of crawled pages
        logger.log(f'Total pages crawled: {len(crawled_pages)}')

        # Upload remaining links in link bank, if they exist
        logger.log(f'Finished crawl for {start_page}.]: Crawl is complete, uploading data to cloud storage.')
        linkBank.upload_remaining_links()

        # Quit the driver to free resources and prevent hanging container.
        driver.quit()

        # Pass an exit code of zero up from the application
        sys.exit(0)

    except Exception as e:
        # Create an instance of Logger class and record exception
        logger.log('Got an exception when attempting to crawl')
        logger.log(e)
        sys.exit(1)





# Extract links from a previously loaded page
def extract_links(driver, current_url):

    links = set()
    try:
        elements = driver.find_elements(By.TAG_NAME, 'a')
        for element in elements:
            link = element.get_attribute('href')
            if link:
                # Check if link is already a full URL
                parsed_link = urlparse(link)
                if parsed_link.scheme and parsed_link.netloc:
                    # Link is already a full URL
                    links.add(link)
                else:
                    # Link is a relative URL, convert it to a full URL
                    full_link = urljoin(current_url, link)
                    links.add(full_link)
    except Exception as e:
        print(f"Error extracting links: {e}")
    return links


def is_external_url(url: str, domain: str) -> bool:
    """
    Check if a given URL is external to a domain.

    Args:
        url (str): The URL to check.
        domain (str): The domain to compare against.

    Returns:
        bool: True if the URL is external to the domain, False otherwise.
    """
    parsed_url = urlparse(url)

    # If the parsed URL has a netloc and it is not a substring of the domain, then the URL is external.
    if parsed_url.netloc and parsed_url.netloc not in domain:
        return True

    # If the parsed URL does not have a netloc, or if the netloc is a substring of the domain, then the URL is internal.
    return False


# Check whether a string representation of a URL starts with mailto:
def is_email_link(url):
    return url.startswith("mailto:")


def stop_and_remove_container():

    hostname = subprocess.check_output('hostname', shell=True).strip().decode('utf-8')

    # If we passed 'True' as an environment var for exitOnFinish, stop and delete the container
    if os.environ.get('exitOnFinish', 'False') == 'True':

        # Get the full path to the Docker executable
        try:
            docker_path = os.environ.get('dockerPath', 'Null')
        except:
            docker_path = 'Null'

        try:
            if docker_path != 'Null':
                # Stop the Docker container
                subprocess.run([docker_path, 'stop', hostname], check=True)

                # Remove the Docker container
                subprocess.run([docker_path, 'rm', hostname], check=True)
            logger.log(f'Shutdown container and removed container with {hostname}')
        except:
            logger.log(f'Failed to shutdown container with {hostname}')
### END OF FUNCTION DEFINITION ###