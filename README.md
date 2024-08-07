Serenity Spider, a headless Chromium based crawler, packaged into a Docker container with an orchestration layer, for crawling multiple websites according to your desired amount of crawling depth + total URL consideration

  1.) git clone https://github.com/lukepollen/serenitySpider
  
  2.) Copy a valid GCP credentials.json object into the WebScraping directory.
  
  3.) Navigate to serenitySpider directory where you will see the requirements.txt and Dockerfile . The Dockerfile will configure a Linux environment with all the required Python libraries.
  
  4.) Start your Docker service on the host system.
  
  5.) docker build -t serenity_spider .
  
  6.) Edit the exampleDockerRun file to contain your relevant credentials and the website to crawl. See the exampleDockerRun.txt and replace with your details.

  7.) (optional) Run the syndicateCrawlers.py with your GCP details and reference to a .xlsx file and watch your GCP tableset fill up with data for each domain.

Commit Five will focus on automatically trying to discover a sitemap at either /sitemap.xml or /sitemap_index.xml .

  
COMMIT FOUR:

Added substantial control updates to the crawler - they can now be syndicated in parallel with Docker and take max_depth and max_url parameters to consider.

This allows for crawling of several websites at once, with the ability to specify how deep into the website, based on url structure (e.g. home page is level 0, home/subject-page is level 1, home/subject-page/topic-in-subject is level 2, etc) and also how much of the website we want to consider.

The internals of the scraper have been updated to pass back a sys.exit(0) on a successful crawl, and a sys.exit(1) on a failed crawl, both of which can be received by the syndication layer via Docker's event bus, allowing for the proper spin up / shut down of crawlers.


COMMIT THREE:

  Multiple quality of like updates.

  1.) Added a LinkBank class, which will now hold 256, uploading when the discovered links is equal or greater to this amount, or the crawl exits. These links will be used in the next crawl of the website, if not already visited within the day number specified (defaults to 30).

  2.) Links to be added to the crawler are now held in sets across the application. This ensures fast insertion as sets are implemented as hashMap in Python, and also that we do not enter duplicate entries. 

  3.) Printing now uses metabeaver's OperationBeaver.logCollector.defaultLogger.Logger class. This will silently write log messages in a logFile directory within the first directory it finds with a setup.py or .git file, traversering upwards. Alternatively, we will write to the app/logFile/log.txt file if we are running the crawler from a Docker container.

  4.) Added a function which takes a set of Links and unpacks them to a pandas dataframe, under a date/time/link address format. 

  5.) Removed redundant init of Chrome driver.


COMMIT TWO:

  Finalised the docker support for the Selenium (Chromium) based crawler. The steps to get the crawler running are as follows: 
  
  1.) git clone https://github.com/lukepollen/serenitySpider
  
  2.) Copy a valid GCP credentials.json object into the WebScraping directory.
  
  3.) Navigate to serenitySpider directory where you will see the requirements.txt and Dockerfile . The Dockerfile will configure a Linux environment with all the required Python libraries.
  
  4.) Start your Docker service on the host system.
  
  5.) docker build -t serenity_spider .
  
  6.) Edit the exampleDockerRun file to contain your relevant credentials and the website to crawl. It currently takes the following format:
 
 docker run -e fullAddress=https://www.britannica.com/ -e crawlDomain=britannica_com -e siteMapLocation= -e parse_type=text -e keyFileLocation=WebScraping/credentials.json -e projectId=your_project_id -e tableSetId=your_bigquery_tableset -e chattyBeaver=False -v "%cd%/logs:/app/logs" serenity_spider
  
  7.) Enjoy life and the Universe, whilst being nice to bees, as your GCP BigQuery database fills up with webcrawl data. So long, thanks for all the fish, and the answer is 42.


COMMIT ONE:
    Initial payload commit.

    Selenium based webcrawling with include and exclude regex filters, dynamic retries, internal web crawling from home page with optional sitemap support, with initial setting specified in the crawl_config.yaml
