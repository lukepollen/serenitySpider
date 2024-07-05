import pandas as pd

import xml.etree.ElementTree as ET

# Function that attempts to parse URLs to crawl from the argument for the location of the sitemap.
def getURLSFromSitemap(sitemapLocation):

    # Container for the sitemap URLs and location of sitemap to crawl
    xmlPairings = []

    # Get the sitemap and extract the data
    tree = ET.parse(sitemapLocation)
    root = tree.getroot()
    print("The number of sitemap tags are {0}".format(len(root)))
    for sitemap in root:
        # children = sitemap.getchildren()
        children = list(sitemap)
        xmlPairings.append({'url': children[
            0].text})  # Could change to add additional items like 'date': children[1].text as k-v pairs to the append

    # Convert parsed data to dataframe and add classification column for the extracted URLs
    try:
        sitemapURLs = pd.DataFrame(xmlPairings)
        allURLs = list(sitemapURLs['url'])
        print('Got ' + str(len(allURLs)) + ' URLs to crawl...')
        print('First URL like:' + str(allURLs[0]))
    except Exception as e:
        print('Could not get a list of URLs to crawl...')
        print(str(e))

    # Return the URLs we processed from the sitemap as a list
    return allURLs