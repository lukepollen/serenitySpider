COMMIT TWO:

  Finalised the docker support for the Selenium (Chromium) based crawler. The steps to get the crawler running are as follows: 
  
  1.) git clone https://github.com/lukepollen/serenitySpider
  
  2.) Copy a valid GCP credentials.json object into the WebScraping directory.
  
  3.) Navigate to serenitySpider directory where you will see the requirements.txt and Dockerfile . The Dockerfile will configure a Linux environment with all the required Python libraries.
  
  4.) Start your Docker service on the host system.
  
  5.) docker build -t serenity_spider .
  
  6.) Edit the exampleDockerRun file to contain your relevant credentials and the website to crawl. It currently takes the following format:
  docker run -e fullAddress=https://www.bumblebee.org/ -e crawlDomain=bumble_bee_org -e siteMapLocation= -e keyFileLocation=WebScraping/your_credentials.json -e projectId=your-gcp-project -e tableSetId=your-bigquery-tableset -v "%cd%/logs:/app/logs" serenity_spider
  
  7.) Enjoy life and the Universe, whilst being nice to bees, as your GCP BigQuery database fills up with webcrawl data. So long, thanks for all the fish, and the answer is 42.


COMMIT ONE:
    Initial payload commit.

    Selenium based webcrawling with include and exclude regex filters, dynamic retries, internal web crawling from home page with optional sitemap support, with initial setting specified in the crawl_config.yaml
