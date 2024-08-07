from urllib.parse import urlparse


# Function which checks whether a string can be parsed to a valid Universal Resource Link
def is_valid_url(url: str) -> bool:
    """
    Check if a given string can be parsed to a valid URL.

    Args:
        url (str): The string to check.

    Returns:
        bool: True if the string can be parsed to a valid URL, False otherwise.
    """
    # Attempt to parse the input URL using urlparse
    try:
        result = urlparse(url)
        # Check if the scheme and netloc components are non-empty
        if all([result.scheme, result.netloc]):
            # If both components are non-empty, the URL is valid
            return True
        else:
            # If either component is empty, the URL is invalid
            return False
    # If urlparse raises a ValueError, the input string is not a valid URL
    except ValueError:
        return False


# Generates base forms of Universal Resource Links, without parameters, and then removes duplicates.
def truncateURLListToBaseForm(urlList):

    # Filter any URLs crawled with ? and # parameters we don't want
    urlList = [x.split('?')[0] for x in urlList]
    urlList = [x.split('#')[0] for x in urlList]

    # Delete copies after reduced URLs to base form
    urlList = list(set(urlList))

    return urlList


def getUrlDepth(start_url, target_url):
    """
    Determine the depth of the target URL relative to the start URL.

    Args:
        start_url (str): The base URL from which the depth is measured.
        target_url (str): The URL whose depth is to be calculated.

    Returns:
        int: The depth of the target URL relative to the start URL.
    """
    # Parse the URLs
    start_parsed = urlparse(start_url)
    target_parsed = urlparse(target_url)

    # Normalize paths by stripping trailing slashes
    start_path = start_parsed.path.rstrip('/').split('/')
    target_path = target_parsed.path.rstrip('/').split('/')

    # Calculate the relative depth
    if target_parsed.netloc != start_parsed.netloc:
        # If target URL's domain is different, it's considered external
        return -1

    # Check if the target path starts with the start path
    if not target_path[:len(start_path)] == start_path:
        # If the target path does not start with the base path, it's not a valid subpath
        return -1

    # Compute the depth
    depth = len(target_path) - len(start_path)

    return depth


if __name__ == '__main__':

    # Test that we successfully judge URL depth 
    def test_get_url_depth():
        start_url = "https://www.home.com"
        test_urls = [
            "https://www.home.com",
            "https://www.home.com/darnassus",
            "https://www.home.com/darnassus/luke-got-an-owl",
            "https://www.home.com/darnassus/the-owl-shop/would-you-like-to-buy-an-owl"
        ]
    
        expected_depths = [0, 1, 2, 3]
    
        for url, expected_depth in zip(test_urls, expected_depths):
            depth = get_url_depth(start_url, url)
            assert depth == expected_depth, f"Expected depth {expected_depth} but got {depth} for URL {url}"
            print(f"{url} - Depth: {depth}")
    
    # Run the test
    test_get_url_depth()