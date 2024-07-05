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
from urllib.parse import urljoin, urlparse

# Imports from Python extended ecosystem
from bs4 import BeautifulSoup
from metabeaver.Formatting.printControl import conditional_print as cprint
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Imports from within project
from WebScraping.universalResourceLinkHandler import is_valid_url


### END Of IMPORTS ###


### FUNCTION DEFINITION ###

def apply_upload(uploadFunc, uploadArgs, pageCrawlData, *args):

    if args:
        if args[0] == 'verbose':
            cprint('\n')
            cprint('in apply_upload...')
            cprint('uploadFunc was ' + uploadFunc.__name__)
            cprint('Upload arguments were: ')
            cprint(uploadArgs)

    uploadFunc(uploadArgs, pageCrawlData)


# Crawl a list of pages, and generate a dictionary like {page : [bodyText, responseLog]}
def crawlPage(driver, eachPage, count, uploadFunc, uploadArgs, *args):

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
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        truthDictionary['wasFullLoaded'] = True
        cprint('Got a fully loaded page:')
        cprint(eachPage)
    # Warn user where we did  not get a document.readyState == complete and / or location of <body> failed
    except Exception as e:
        print(eachPage)
        print('Wait for page load failed')
        cprint(f'While waiting for page load, got a generic Exception waiting for the page: {str(e)}')

        count = count - 1

        # Try to recursively crawl the page if failed attempts not equal to count
        if count > 0:
            crawlPage(driver, eachPage, count, uploadFunc, uploadArgs, *args)
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
        # Extract all visible text
        page_text = soup.get_text(separator='\n', strip=True)
        #page_text = driver.find_element(By.XPATH, '//body').text

        # Update the crawl data with the page text we've parsed from the raw HTML.
        pageCrawlData[1] = page_text
        truthDictionary['gotBodyText'] = True
        cprint('Got pageText.')
    # Try to recursively crawl a page on a timeout of retrieving body text
    except (TimeoutException, WebDriverException) as e:

        # Warn on failed attempt to driver.get() a page due to timeout
        print(eachPage)
        print('Hit a TimeoutException or WebDriverException!')
        cprint(f'While retrieving loaded page data, got an TimeoutException or WebDriverException: {str(e)}')
        count = count - 1

        # Try to recursively crawl the page if failed attempts not equal to count
        if count > 0:
            crawlPage(driver, eachPage, count, uploadFunc, uploadArgs, *args)
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
        print(eachPage)
        print(f'While retrieving loaded page data, got a generic Exception: {str(e)}')

        # Attempt a recursive crawl
        if count > 0:
            count = count - 1
            crawlPage(driver, eachPage, count, uploadFunc, uploadArgs, *args)
        else:
            pageCrawlData = [eachPage,
                             'Failed to crawl page due to Exceptions',
                             'No network response',
                             truthDictionary,
                             date,
                             time]


    # Get the response log. Extract the HTTP code, and store the full log.
    try:
        responseLog = driver.get_log('performance')
        pageCrawlData[2] = responseLog
        truthDictionary['gotResponseLog'] = True
    # Use default warning value on failed response log retrieval steps
    except Exception as e:

        print(eachPage)
        print('Could not retrieve the response log!')

        # Store error value for the response log if we could not retrieve network values
        pageCrawlData[2] = 'Could not retrieve the response log!'
        cprint(f'While trying to retrieve driver log, got a generic Exception: {str(e)}')
        cprint('Could not retrieve the response log!')

    # If we got a fully loaded page, text from the body, with a network log and HTTP code, consider crawl a success.
    if (truthDictionary.get('wasFullLoaded') == True and
            truthDictionary.get('gotBodyText') == True and
            truthDictionary.get('gotResponseLog') == True and
            truthDictionary.get('gotWebCode') == True):
        truthDictionary['successfulComplete'] = True

    # Replace line break symbol with an actual gap in the text.
    try:
        page_text = page_text.replace("\n", " ")
        pageCrawlData[1] = page_text
    except UnboundLocalError as ule:
        print(f'While replacing newlines in the retrieved page_text, got an UnboundLocalError:  {str(ule)}')
        pageCrawlData[1] = ''

    # Print the progress if we asked metabeaver.formatting.conditionalPrint to be talkative
    cprint('\n')
    cprint('The page was: ' + eachPage)

    # Conditionally print the status of the call, if we have a talkative beaver.
    cprint('\n')
    for k, v in truthDictionary.items():
        cprint('Printing page crawl milestones')
        cprint(k + ' : ' + str(v))

    # Create a string that gives the truth values for each stage of potential success
    pageCrawlData[3] = ', '.join([f"{key}: {value}" for key, value in truthDictionary.items()])

    # Send the crawled data to the cloud
    if os.environ['BEAVER_PRINTING'] == 'TRUE':
        apply_upload(uploadFunc, uploadArgs, pageCrawlData, 'verbose')
    else:
        apply_upload(uploadFunc, uploadArgs, pageCrawlData)

    # Return the driver, in case we are crawling from the homepage, or wish to perform other actions on loaded page
    return driver


# Crawl a website by starting from the home page
def crawl_website(driver,
                  start_page,
                  additionalPages,
                  filterPages,
                  count,
                  uploadFunc,
                  uploadArgs,
                  linkUploadFunc,
                  linkUploadArgs,
                  patternList=['.*'],
                  printMode='verbose',
                  *args):

    # Alert the user to the page we will start with
    cprint('Start page is: ' + start_page)

    # Container to hold data for when we discovered links
    linkTimeData = []
    # Get today's date as a string to add to the links to crawl
    todayDate = dt.datetime.today().strftime('%Y-%m-%d')
    # Get today's time as a string to add to the links to crawl
    todayTime = dt.datetime.today().strftime('%Y-%m-%d')
    # Append these elements so we know when a link on a page was discovered.
    linkTimeData.append(todayDate)
    linkTimeData.append(todayTime)

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
    cprint('Total pages to crawl is: ' + str(len(pages_to_crawl)))

    # Base domain to reference when examining links
    domain = urlparse(start_page).netloc

    # While we have discovered pages we have not yet crawled, continue crawling
    while pages_to_crawl:

        # Get the next page to crawl
        page = pages_to_crawl.pop()

        # Check if the page has already been crawled
        if page not in crawled_pages:

            # Crawl the page
            driver = crawlPage(driver, page, count, uploadFunc, uploadArgs, *args)
            # Add the page to the set of crawled pages
            crawled_pages.append(page)

            # Extract links from the page
            new_links = extract_links(driver, page)
            cprint('New links were: ')
            cprint(new_links)

            # Only add new links to crawl which are same domain
            for link in new_links:
                # Do not add link if we've already crawled.
                if link not in crawled_pages:
                    cprint('Adding link, ' + str(link))
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
                                cprint('Got a valid link to append!')

                                # Continue to the next link to check if we did not get a valid link on this iteration.
                                if not stillValidLink:
                                    continue

                                # Add link to crawl location
                                pages_to_crawl.add(link)

                                ## Send the new link to the upload destination
                                # Add link and time/date to list. Upload the link-date-time combination to the cloud.
                                linkTimeData.append(link)

                                # Upload Link Data.
                                linkUploadFunc(linkUploadArgs, linkTimeData)
                                cprint('Uploaded link data to the cloud!')
                                cprint(linkTimeData)

                                # Remove Link for next iteration.
                                linkTimeData.pop(2)

    # Print the total number of crawled pages
    print(f'Total pages crawled: {len(crawled_pages)}')


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


# Take an URL represented as a string and the domain name and check whether potential URL in same domain
#def is_external_url(url, domain):
#    parsed_url = urlparse(url)
#    if parsed_url.netloc and parsed_url.netloc != domain:
#        return True
#    return False


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


### END OF FUNCTION DEFINITION ###