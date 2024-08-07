import docker
import os
import time
import concurrent.futures
import pandas as pd
import re

def validate_url(url):
    return bool(url_pattern.match(url))

def run_crawler(domain):
    try:
        print(f'Creating crawler for {domain}')
        full_address = domain
        crawl_domain = domain.split('//')[1].replace('.', '_')

        container = client.containers.run(
            "clockwork_spider",
            detach=True,
            environment={
                "fullAddress": full_address,
                "crawlDomain": crawl_domain,
                "siteMapLocation": "",
                "parse_type": "text",
                "keyFileLocation": "WebScraping/credentials.json",
                "projectId": "your-gcp-project",
                "tableSetId": "your-gcp-tableset",
                "chattyBeaver": "False",
                "maxDepth": "3",
                "maxURLs": "100",
            },
            volumes={
                f"{os.getcwd()}/logs": {
                    'bind': '/app/logs',
                    'mode': 'rw'
                }
            },
            stdout=True,
            stderr=True
        )
        print(f'Created the container {container.id} for {domain}')

        try:
            print(f'Waiting for container {container.id} to finish...')
            result = container.wait(timeout=1200)
            logs = container.logs().decode('utf-8')
            print(f"Logs for container {container.id}:\n{logs}")
        except (docker.errors.ContainerError, docker.errors.APIError, Exception) as e:
            print(f"Error waiting for container {container.id}: {e}")

            # Retrieve and print logs before stopping and removing the container
            logs = container.logs().decode('utf-8')
            print(f"Logs for container {container.id}:\n{logs}")

            # Stop container if not stopped and then remove the container
            if container.status != 'exited':
                container.stop()
            container.remove()
            return

        print(f'Container {container.id} finished waiting.')

        exit_code = result["StatusCode"]
        print(f'Got an exit code from container {container.id}: {exit_code}')

        if exit_code == 0:
            print(f"Container {container.id} finished crawling {domain} successfully")
        else:
            print(f"Container {container.id} failed to crawl {domain} with exit code {exit_code}")

        container.stop()
        container.remove()
        print(f'Removed container {container.id} for {domain}')

    except Exception as e:
        print(f"Exception occurred while running crawler for {domain}: {e}")
        if 'container' in locals() and container.status != 'exited':
            container.stop()
            container.remove()

    return None

file_path = r'youMustPlaceAValidFilePathHerePadawan\yourDomains.xlsx'
n_concurrent = 6

if __name__ == '__main__':
    df = pd.read_excel(file_path)
    print(df)

    # Prepend 'https://www.' if not already present
    def prepend_url(url):
        if not url.startswith('https://www.'):
            return f'https://www.{url}'
        return url

    df.iloc[:, 0] = df.iloc[:, 0].apply(prepend_url)

    url_pattern = re.compile(r'^https://www\.[a-zA-Z0-9\-]+\.[a-zA-Z]{2,6}(/)?$')
    df['is_valid'] = df.iloc[:, 0].apply(validate_url)
    print(df)
    valid_urls_df = df[df['is_valid']].iloc[:, 0]
    valid_urls_list = valid_urls_df.tolist()
    domains = list(set(valid_urls_list))
    print(domains)
    client = docker.from_env()

    with concurrent.futures.ThreadPoolExecutor(max_workers=n_concurrent) as executor:
        futures = [executor.submit(run_crawler, domain) for domain in domains]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Exception in future result: {e}")