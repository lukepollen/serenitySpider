import datetime as dt
import os
import time

from metabeaver.Formatting.printControl import conditional_print as cprint

# Function to periodically check the driver status
def check_driver_status(start_time, driver):

    # Enter a loop which will, every five minutes, check whether the crawler ran out of memory
    while True:

        # Check if 5 minutes or more have passed since the start time
        current_time = dt.datetime.now()
        elapsed_time = (current_time - start_time).total_seconds() / 60  # Elapsed time in minutes
        print('elapsed_time is now: ' + str(elapsed_time))

        # Every five minutes check whether we hit the Chrome error page.
        if elapsed_time >= 5:
            cprint("5 minutes have passed. Checking for 'Aw, Snap!' and reinitializing if needed.")

            # Check if the page has "Aw, Snap!" error
            if 'Aw, Snap!' in driver.page_source:
                print('Reinitializing the driver due to "Aw, Snap!" error.')

                # Close the current driver, because it's broken and most likely out of memory.
                driver.quit()

                # Run controlFile.py script (replace 'python controlFile.py' with the actual command)
                os.system('python controlFile.py')

        # Sleep for some time before checking again (adjust as needed)
        time.sleep(300)  # Sleep for 5 minutes (300 seconds)


























