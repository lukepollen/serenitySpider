from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


def instantiateDriver():

    # Specify the options we want to use in the selenium web crawler
    options = Options()
    options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"    #chrome binary location specified here
    options.add_argument('--enable-logging --v=1')
    options.add_argument("--start-maximized") # Open Browser in maximized mode
    options.add_argument("--no-sandbox") # Bypass OS security model
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    noTrack = {"enable_do_not_track": True} # reduce network payload and spam on analytics
    options.add_experimental_option("prefs", noTrack)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Specify desired capacities, e.g. include logging
    d = DesiredCapabilities.CHROME
    d['goog:loggingPrefs'] = { 'performance':'ALL' }


    # Instantiate driver object from webdriver.Chrome, and get an URL
    driver_service = Service(executable_path=r'C:\Users\lukep\OneDrive\Maths and Sci Code\Software Dev\Web\Selenium\chrome-win64\chrome-win64\chrome.exe')
    driver = webdriver.Chrome(service=driver_service,
                              options=options,
                              desired_capabilities=d,
                              )

    return driver


def initiateDriver():

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    no_track = {"enable_do_not_track": True}
    options.add_experimental_option("prefs", no_track)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    d = webdriver.DesiredCapabilities.CHROME
    d['goog:loggingPrefs'] = {'performance': 'ALL'}

    # Install the correct driver.
    # driver_manager = ChromeDriverManager()
    # driver = webdriver.Chrome(ChromeDriverManager().install(),
    #                           service=driver_manager.service,
    #                           options=options,
    #                           desired_capabilities=d)

    driver = webdriver.Chrome(options=options)

    return driver