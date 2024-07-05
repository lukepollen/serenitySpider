import yaml

# Will return a dictionary of data that can be passed to the high level controlFile for establishing crawl settings.
def returnCrawlConfigData():
    # Load configuration from the YAML file
    with open('crawl_config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    home_address = config.get('homeAddress', '')
    website_name = config.get('websiteName', '')
    site_map_location = config.get('siteMapLocation', '')
    key_file_loc = config.get('keyFileLoc', '')
    project_id = config.get('projectId', '')
    table_set_id = config.get('tableSetId', '')

    metaData = {
        'homeAddress': home_address,
        'websiteName': website_name,
        'siteMapLocation': site_map_location,
        'keyFileLoc': key_file_loc,
        'projectId': project_id,
        'tableSetId': table_set_id
    }

    return metaData

# Example usage
if __name__ == "__main__":
    config_data = returnCrawlConfigData()
    print(config_data)
