#!/usr/bin/env python
#################### START IMPORTS ####################
import selenium.webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from concurrent.futures import ThreadPoolExecutor, wait
import json
import time
from datetime import date
from datetime import timedelta
from progress.bar import Bar
import argparse
import config
#################### END IMPORTS ####################

#################### START CONSTANTS ####################
SHIBBOLETH_USERNAME = config.username
SHIBBOLETH_PASSWORD = config.password
CHROME_DRIVER_LOCATION = "./chromedriver"
COOKIE_PATH = "./cookies.json"
NELSON_ID = "n"
NELSON_NAME = "Nelson"
SWIM_ID = "s"
SWIM_NAME = "Swim"
NELSON_BOOKING_URL = "https://bfit.brownrec.com/booking/4a42ba76-754b-48c9-95fd-8df6d4e3fb4d"
SWIM_BOOKING_URL = "https://bfit.brownrec.com/booking/25de03fb-15e3-429d-bd3c-9483cc821ad5"
LOADING_WAIT_DUR = 10
#################### END CONSTANTS ####################

#################### START HELPERS ####################
def parse_args():
    parser = argparse.ArgumentParser(description='Bfit Auto Booker')
    parser.add_argument('-nelson', help="number of threads you want to use to book nelson slots", default=0)
    parser.add_argument('-swim', help="number of threads you want to use to book swim slots", default=0)
    parser.add_argument('-daysfromnow', help='which day you want between [0, 3] where 0 is today, 3 is three days from now', default=3)
    parser.add_argument("-dayofweek", help="enter the day you want by name with only the first 3 letters (e.g., 'wed', 'tue', 'mon')", default=None)
    parser.add_argument("-headless", help="enter y for no gui; enter n for gui.", default="y")
    parser.add_argument("-stoponbook", help="enter y to stop all threads on a successful book, n otherwise.", default="y")
    # parser.add_argument('-all', help='enter y to search all dates for a reservation; n otherwise', default="n") # TODO: add ability to go through all days...
    return parser.parse_args()

def try_accept_gdpr_cookie(driver):
    """
    Accepts the GDPR cookie on Bfit -- necessary for functionality.

    Args:
        driver (Driver): The instance of the web driver being used.

    Returns:
        Nothing.
    """
    driver.find_element_by_id("gdpr-cookie-accept").click() #TODO: error check

def check_for_reservation(driver):
    """
    If there exists a "booking-slot-reserved-item," then the user has a reservation.

    Args:
        driver (Driver): The instance of the web driver being used.

    Returns:
        Nothing.
    """
    return len(driver.find_elements_by_class_name("booking-slot-reserved-item")) > 0

def button_disabled(element):
    """
    For some WebElement, check whether or not it is disabled. 
    In this case, the element should have 'disabled' ONLY as the last class selector.

    Args:
        element (WebElement): Some webelement, likely a reservation button.
    
    Returns:
        true if disabled, false if enabled.
    """
    # Last element should be "disabled"; optimized to only search last element.
    return "disabled" in element.get_attribute("class").split()[-1:]

def save_cookie(driver, path):
    """
    Creates a JSON file that contains the cookies saved within Driver currently.

    Args:
        driver (Driver): The instance of the web driver being used.
        path (String): Path to the JSON file to save.

    Returns:
        Nothing (writes to file).
    """

    with open(path, 'w') as filehandler:
        json.dump(driver.get_cookies(), filehandler)

def load_cookie(driver, path):
    """
    Loads a JSON file that contains the cookies saved previously within an old driver instance.
    These cookies are then added to the passed in driver.

    Args:
        driver (Driver): The instance of the web driver being used.
        path (String): Path to the JSON file to load.

    Returns:
        Nothing (adds cookies to driver).
    """
    with open(path, 'r') as cookiesfile:
        cookies = json.load(cookiesfile)
    for cookie in cookies:
        driver.add_cookie(cookie)

def print_driver_source_to_txt(driver, path):
    """
    Writes the page source of the current driver instance to file.

    Args:
        driver (Driver): The instance of the web driver being used.
        path (String): Path to the file to save.

    Returns:
        Nothing (writes to file).
    """
    with open(path, 'w') as f1:
        f1.write(driver.page_source)

def successful_book(driver, book_btn):
    """
    Checks whether or not the reservation slot was successful or not.

    Args:
        driver (Driver): The instance of the web driver being used.
        book_btn (WebElement): The reservation button clicked on.

    Returns:
        true if disabled, false if not.
    """
    # TODO: double check this works in all cases
    return book_btn.get_attribute("disabled") != None # book button disables itself on a successful click. # TODO: may have to handle "Booking..." text in case of network lag.
    # return driver.find_element_by_id("alertBookingSuccess").get_attribute("hidden") == None # check to see if a success alert popped up

def try_load_chrome(reservation_url, is_headless):
    """
    Creates a driver instance (of Chrome), loads cookies if they exist,
    and then attempts to sign-in. This should bring the user to the reservation
    page they chose. If no cookies exist, it will return early and reset itself elsewhere.

    Args:
        reservation_url (String): The URL of the reservation page.
        is_headless (bool): Whether the program is headless or not (headless == no GUI)

    Returns:
        The constructed driver instance with the reservation page loaded OR a driver with no cookies (error case).
    """
    print("Loading Chrome...")
    # Create chrome instance & load cookies
    driver = create_driver_instance(reservation_url, is_headless)

    try:
        load_cookie(driver, COOKIE_PATH)
    except:
        return driver
    driver.refresh()

    # Try login
    try:
        driver.find_element_by_xpath('//button[normalize-space()="Brown Username"]').click()
    except: # no login button exists; probably caused by logining in and not restarting.
        driver.get(reservation_url) # try reloading the nelson booking!
    
    return driver

def get_date_options(driver):
    """
    Populates a map with a mapping of {day_by_name, date button}; this allows us to access the specific 
    date button for some day (e.g., "give me the button for Wednesday")

    Args:
        driver (Driver): The instance of the web driver being used.

    Returns:
        Populated map {day_by_name, date button}
    """
    date_options = {}
    date_container = driver.find_elements_by_class_name("single-date-select-one-click")
    for datebtn in date_container:
        day_by_name = datebtn.find_element_by_class_name("single-date-select-button-day").get_attribute('innerHTML').lower() # not .text; doesn't work on headless w/ screen size small.
        date_options[day_by_name.lower()] = datebtn
    return date_options

def try_load_dates(reservation_url, driver, is_headless):
    """
    Handles loading a map of date buttons. If the loading fails, then it is likely because of a cookies issue, and not being
    able to access the reservation page; in this case, chrome is reset, cookies are reloaded (the user must auth again), and
    the resultant dates are returned.

    Args:
        reservation_url (String): The URL of the reservation page.
        driver (Driver): The instance of the web driver being used.
        is_headless (bool): Whether the program is headless or not (headless == no GUI)

    Returns:
        (driver, date_options) tuple, containing the web driver (which could have been reset), and a map of {day_by_name, date button}.
    """
    # Dates for chrome
    print("Getting all dates for reservation page...")
    date_options = get_date_options(driver)
    if len(date_options) < 4: # always 4 dates at least
        (driver, date_options) = reset_cookies_load_chrome_and_dates(reservation_url, driver, is_headless)
    return (driver, date_options) # updated driver, if at all

def try_load_dates_no_error(driver):
    """
    Identical to try_load_dates except that it does NOT reset chrome or cookies. This function should be used if it is expected that
    the page is simply loading slowly, not that there is a cookie issue potentially.

    Args:
        driver (Driver): The instance of the web driver being used.

    Returns:
        (driver, date_options) tuple, containing the web driver, and a map of {day_by_name, date button}.
    """
    # Dates for chrome
    date_options = get_date_options(driver)
    if len(date_options) < 4: # always 4 dates at least 
        return try_load_dates_no_error(driver) # try again
    return (driver, date_options) # updated driver, if at all

def load_chrome_and_dates(reservation_url, is_headless):
    """
    Loads a ChromeDriver instance, and then loads any relevant date options for the reservation page.

    Args:
        reservation_url (String): The URL of the reservation page.
        is_headless (bool): Whether the program is headless or not (headless == no GUI)

    Returns:
        (driver, date_options) tuple, containing the Chrome web driver, and a map of {day_by_name, date button}.
    """
    driver = try_load_chrome(reservation_url, is_headless)
    return try_load_dates(reservation_url, driver, is_headless)

def handle_shibboleth_login(driver):
    """
    Assuming the user is locked out of the reservation page, this will click login, enter any info
    (IMPORTANT: MAKE SURE TO FILL OUT sample_config.py AND RENAME IT config.py), and then login.
    This requires authentication on the user's end, manually.

    Args:
        driver (Driver): The instance of the web driver being used.

    Returns:
        Nothing
    """
    # Login information screen
    driver.find_element_by_xpath('//button[normalize-space()="Brown Username"]').click()
    username = driver.find_element_by_id("username")
    password = driver.find_element_by_id("password")

    username.send_keys(SHIBBOLETH_USERNAME)
    password.send_keys(SHIBBOLETH_PASSWORD)

    driver.find_element_by_name("_eventId_proceed").click() # Submit login

    # Wait for duo push success
    wait_for_verification(driver)

def wait_for_verification(driver):
    """
    Waits for the user to authenticate via Duo (or equivalent).
    Impossible to manually fire the "Send Push" button due to JS limitations
    (or at least, I couldn't figure it out -- someone help!).
    Times out if the user doesn't auth.

    Args:
        driver (Driver): The instance of the web driver being used.

    Returns:
        Nothing
    """
    # save current page url
    current_url = driver.current_url

    print("Please login. Authenticate however you want!")

    # wait for URL to change with 30 seconds timeout
    WebDriverWait(driver, 300).until(EC.url_changes(current_url))

def create_headless_chrome(reservation_url):
    """
    Creates an instance of Chrome WebDriver without a GUI.
    GPU disabled for compatability (according to Googling), 
    JS enabled to have pages load as much as possible,
    window size is 1920x1080 to ensure page sizes don't trigger mobile layouts.

    Args:
        reservation_url (String): The URL of the reservation page.

    Returns:
        Instantiated headless Chrome Web Driver.
    """
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--enable-javascript')
    options.add_argument('--window-size=1920,1080')

    caps = DesiredCapabilities().CHROME
    # caps["pageLoadStrategy"] = "normal"  #  complete
    caps["pageLoadStrategy"] = "eager"  #  interactive
    driver = selenium.webdriver.Chrome(CHROME_DRIVER_LOCATION, options=options, desired_capabilities=caps)
    driver.implicitly_wait(LOADING_WAIT_DUR)
    driver.get(reservation_url)
    return driver

def create_chrome_with_gui(reservation_url):
    """
    Creates an instance of Chrome WebDriver with a GUI.
    JS enabled to have pages load as much as possible,
    window size is 1920x1080 to ensure page sizes don't trigger mobile layouts.

    Args:
        reservation_url (String): The URL of the reservation page.

    Returns:
        Instantiated Chrome Web Driver with GUI.
    """
    options = Options()
    options.add_argument('--enable-javascript')
    options.add_argument('--window-size=1920,1080')
    driver = selenium.webdriver.Chrome(CHROME_DRIVER_LOCATION, options=options)
    driver.implicitly_wait(LOADING_WAIT_DUR)
    driver.get(reservation_url)
    return driver

def create_driver_instance(reservation_url, is_headless):
    """
    Creates an instance of Chrome WebDriver, GUI / headless depending on is_headless.

    Args:
        reservation_url (String): The URL of the reservation page.
        is_headless (bool): Whether the program is headless or not (headless == no GUI)

    Returns:
        Instantiated Chrome Web Driver with GUI.
    """
    if (is_headless):
        return create_headless_chrome(reservation_url)
    return create_chrome_with_gui(reservation_url)

def reset_cookies_load_chrome_and_dates(reservation_url, old_driver, is_headless):
    """
    First, closes the old driver, and then creates a temporary driver to enable authentications.
    Once auth'ed, saves cookies, resets the driver, and then continues with the newly loaded driver.
    This guarantees that whatever driver instance is used after this function MUST HAVE COOKIES and
    MUST be logged in properly.

    Args:
        reservation_url (String): The URL of the reservation page.
        old_driver (Driver): The instance of the web driver being used.
        is_headless (bool): Whether the program is headless or not (headless == no GUI)

    Returns:
        (driver, date_options) tuple, containing the Chrome web driver, and a map of {day_by_name, date button}.
    """
    old_driver.close()
    driver = create_driver_instance(reservation_url, False) # Always with GUI for auth purposes

    # Login
    handle_shibboleth_login(driver)

    # Save cookies after shibboleth
    # Accept cookies so the slot can actually be accepted lol
    try_accept_gdpr_cookie(driver)
    save_cookie(driver, COOKIE_PATH)
    driver.close()
    return load_chrome_and_dates(reservation_url, is_headless)

def try_book_slot(driver, book_btn):
    """
    Clicks on the book_btn, and returns whether it was a successful attempt.

    Args:
        driver (Driver): The instance of the web driver being used.
        book_btn (WebElement): The reservation button clicked on.

    Returns:
        true if reserved, false if not.
    """
    book_btn.click() # TODO: error check, could be invalid.
    # Confirm whether or not we got the slot... 
    return successful_book(driver, book_btn)

def select_reservation_date(date_options, days_from_now):
    """
    Determines the target reservation date based on days_from_now, and then 
    attempts to refresh the screen so that the slots displayed are for that specific
    reservation date.

    Args:
        date_options (Map<String, WebElement>): A map from [day_by_name, book_btn]
        days_from_now (int): The number of days from today the target reservation date lies on (e.g., today == 3/6/2021, target=3/9/2021, days_from_now == 3)

    Returns:
        (str) reservation date by name.
    """
    print("Selecting reservation date...")
    reservation_date = date.today() + timedelta(days=days_from_now)
    reservation_date_by_name = reservation_date.strftime('%A')[:3].lower() # BFit does names using first 3 letters
    if (reservation_date_by_name in date_options):
        print("Reservation date selected:", reservation_date_by_name)
        refresh_reservation_date(date_options, reservation_date_by_name)
    else: 
        print("No reservations available yet for:", reservation_date_by_name)
    return reservation_date_by_name

def select_reservation_date_by_name(date_options, reservation_date_by_name):
    """
    Attempts to refresh the screen so that the slots displayed are for that specific
    reservation date. Uses a predetermined reservation date instead of calcuating it.

    Args:
        date_options (Map<String, WebElement>): A map from [day_by_name, book_btn]
        reservation_date_by_name (str): the name of the day of the week the user wants

    Returns:
        (str) reservation date by name.
    """
    print("Selecting reservation date...")
    if (reservation_date_by_name in date_options):
        print("Reservation date selected:", reservation_date_by_name)
        refresh_reservation_date(date_options, reservation_date_by_name)
    else: 
        print("No reservations available yet for:", reservation_date_by_name)
    return reservation_date_by_name

def refresh_reservation_date(date_options, reservation_date_by_name):
    """
    Clicks on the reservation date button if it exists.

    Args:
        date_options (Map<String, WebElement>): A map from [day_by_name, book_btn]
        reservation_date_by_name (str): the name of the day of the week the user wants

    Returns:
        (str) reservation date by name.
    """
    # Optimized for Bfit -- clicking on a date refreshes buttons; no need to refresh whole page. Simply click on the correct date.
    # Make sure the correct day is selected visually 
    if date_options[reservation_date_by_name.lower()] != None:
        date_options[reservation_date_by_name.lower()].click()

def get_reservation_url(id):
    """
    Parses the args passed in to determine the reservation URL.

    Args:
        id (str): The ID of the reservation page we're looking for (e.g., NELSON_ID)
    
    Returns:
        (str) reservation url.
    """
    reservation_url = ""
    if (id == NELSON_ID):
        reservation_url = NELSON_BOOKING_URL
    elif (id == SWIM_ID):
        reservation_url = SWIM_BOOKING_URL
    return reservation_url

def get_day_of_week_from_args(args):
    """
    Parses the args to get the desired reservation day.

    Args:
        args (args): Args supplied via command line.

    Returns:
        (str) reservation day by name.
    """
    if (args.dayofweek == None):
        return None
    return args.dayofweek.lower() # make sure lower

def hydrate_from_args(args, id):
    """
    Returns a tuple of all relevant args from the parsed command line args.

    Args:
        args (args): Args supplied via command line.
        id (str): The ID of the reservation page we're looking for (e.g., NELSON_ID)

    Returns:
        tuple containing relevant arguments, parsed.
    """
    # Hydrate 
    reservation_url = get_reservation_url(id)
    days_from_now = int(args.daysfromnow)
    is_headless = args.headless.lower() == "y"
    dayname = get_day_of_week_from_args(args)
    return (reservation_url, days_from_now, is_headless, dayname)

def id_to_name(id):
    """
    Returns a human readable version of the ID passed in

    Args:
        id (str): Some ID like NELSON_ID

    Returns:
        (str) version that is more human readable / understandable.
    """
    if (id == NELSON_ID):
        return NELSON_NAME
    elif (id == SWIM_ID):
        return SWIM_NAME

def should_stop_on_book(stop_on_book):
    """
    Returns whether or not all threads should stop on a single successful book or not.

    Args:
        stop_on_book (str): Arg that's one of {y, n}
    
    Returns:
        (bool) true if should stop, false if should continue.
    """
    return stop_on_book == "y"
    
def try_book_for_day(driver, date_options, reservation_date_by_name, ideal_times, should_stop):
    """
    Gets the most up to date information for the current reservation date passed in, and then 
    searches for a valid reservation slot according to (1) if it is available, and (2) if the user 
    wants the slot via config.py. If a valid slot, it attempts to book it.
    This function returns once a slot is booked, or all slots have been checked.

    Args:
        driver (Driver): The instance of the web driver being used.
        date_options (Map<String, WebElement>): A map from [day_by_name, book_btn]
        reservation_date_by_name (str): the name of the day of the week the user wants
        ideal_times (Set<String>): a set containing all reservation times the user wants for reservation_date_by_name.
        should_stop (bool): whether or not booking should continue after a reservation is detected.

    Returns:
        True if booked, false if not booked.
    """
    # Get the most up to date booking info
    refresh_reservation_date(date_options, reservation_date_by_name)

    # Get all slots for that date
    booking_slots = driver.find_element_by_id("divBookingSlots").find_elements_by_class_name("booking-slot-item")

    # Attempt to book each slot
    booking_text = "Attempting to book one of " + str(len(booking_slots)) + " slots:"
    bar = Bar(booking_text, max=len(booking_slots))
    
    for slot in booking_slots:
        try:
            book_btn = slot.find_element_by_tag_name("button")
        except:
            continue
        try:
            if not button_disabled(book_btn): # Make sure the slot is available...
                # Get the time slot for this specific button
                time_slot = slot.find_element_by_tag_name("p").text

                # Go through all timeslots for the reservation day, attempt to book
                for target_time_slot in ideal_times:
                    if time_slot == target_time_slot:
                        print("\nAttempting to book", reservation_date_by_name, "at", target_time_slot)
                        booked = try_book_slot(driver, book_btn)
                        # Return if booked successfully or stop early if booked previously (not caught by selenium)
                        if (booked or (should_stop and slot.find_element_by_class_name("text-primary").text.strip().lower() == "booked")):
                            bar.finish()
                            return True
            bar.next()
        except: # probably caused by the booking being unsuccessful. Go to next slot.
            bar.next()
            continue
    bar.finish()
    return False # Didn't book this day :(

def multithread_book_single_day(args):
    """
    Same as book_single_day, except multithreaded.

    Args:
        args (args): Args supplied via command line.
    
    Returns:
        Nothing
    """
    # Arguments for number of nelson / swim threads
    num_nelson_threads = int(args.nelson)
    num_swim_threads = int(args.swim)

    # Handle no threads requested
    if (num_nelson_threads <= 0 and num_swim_threads <= 0):
        print("ERROR: Please request at least one thread for one of {nelson, swim} reservations. For example, '-nelson 5' creates 5 threads for Nelson reservations.")
        return

    # Multithread reservations
    with ThreadPoolExecutor() as executor:
        # Generate threads for Nelson reservations
        print("Starting NELSON threads...")
        if (num_nelson_threads > 0):
            for t_count in range(num_nelson_threads):
                print(f"Starting thread#{t_count}")
                executor.submit(book_single_day, args, NELSON_ID, t_count)

        # Generate threads for Swim reservations
        if (num_swim_threads > 0):
            print("Starting SWIM threads...")
            for t_count in range(num_swim_threads):
                print(f"Starting thread#{t_count + num_nelson_threads}")
                executor.submit(book_single_day, args, SWIM_ID, t_count + num_nelson_threads)
        

def book_single_day(args, id, thread_num):
    """
    Attempts to book a single day according to the params provided.

    Args:
        args (args): Args supplied via command line.
        id (str): The ID of the reservation page we're looking for (e.g., NELSON_ID)
        thread_num (int): the thread number assigned to this function

    Returns:
        Nothing
    """
    # Hydrate 
    (reservation_url, days_from_now, is_headless, dayofweek) = hydrate_from_args(args, id)
    readable_facility_name = id_to_name(id)

    # Load chrome instance w/ cookies.
    (driver, date_options) = load_chrome_and_dates(reservation_url, is_headless)

    # Make sure the correct date is chosen before beginning
    if (dayofweek != None):
        reservation_date_by_name = select_reservation_date_by_name(date_options, dayofweek)
    else:
        reservation_date_by_name = select_reservation_date(date_options, days_from_now)
    
    attempt_num = 0
    booked = False
    should_stop = should_stop_on_book(args.stoponbook)

    # Load the ideal time slots from the relevant config 
    ideal_times = []
    if (reservation_url == NELSON_BOOKING_URL):
        ideal_times = config.target_nelson_time_slots[reservation_date_by_name]
    else:
        ideal_times = config.target_swim_time_slots[reservation_date_by_name]
    
    while not booked: # while didn't book, keep trying!
        print("--------------")
        print(f"Starting attempt {attempt_num} for {readable_facility_name} via thread#[{thread_num}]")
        
        # Handle cases where the target reservation date doesn't exist on the page yet
        # Essentially refreshes until the reservation date exists in the set of dates on the Bfit page.
        while (reservation_date_by_name not in date_options):
            print("Refreshing to get new reservation dates...")
            driver.refresh()
            (driver, date_options) = try_load_dates_no_error(driver)

        booked = try_book_for_day(driver, date_options, reservation_date_by_name, ideal_times, should_stop)
        if (booked): # or check_for_reservation(driver)
            print("You have a slot! Ending thread now!")
            print("xxxxxxxxxxxxxxxxx")
            booked = True
        else:
            print("Attempt", attempt_num, "failed :(. Trying again.")
            attempt_num += 1
    
    try:
        driver.close()
    except:
        print("Goodbye! (Although, you already closed me :(")

def book_single_day_benchmark(args):
    """
    Benchmark for booking a single day -- basically tests how long it takes to get through a single book_single_day function call.

    Args:
        reservation_url (String): The URL of the reservation page.
        days_from_now (int): The number of days from today the target reservation date lies on (e.g., today == 3/6/2021, target=3/9/2021, days_from_now == 3)
        is_headless (bool): Whether the program is headless or not (headless == no GUI)

    Returns:
        Nothing
    """
    sum = 0
    for i in range(10):
        t0 = time.time()
        book_single_day(args)
        t1 = time.time()
        diff = t1-t0
        print(f"Total execution time for step {i}: {diff}")
        sum += diff
    print("avg:", sum/10)

#################### END HELPERS ####################

#################### MAIN ####################
def main():
    ################ SUGGESTED USAGES ################
    # (assumes in gym_venv, activate via: source ~/gym_venv/bin/activate; setup via ./create_venv.sh; make sure Python 3.7):
    # python3.7 signup.py -nelson 5 -swim 5 -dayofweek mon 
    #       this will spin up 10 threads: 5 dedicated to booking nelson slots, 5 for swim slots. All looking for monday. In headless mode.
    # 
    # python3.7 signup.py -nelson 1 -dayofweek mon
    #       this will spin up 1 thread for looking for a monday Nelson slot
    #       **IF YOU HAVEN'T RUN THIS IN A WHILE, USE THIS. OTHERWISE AUTHENTICATION WILL SPAM A BUNCH OF WINDOWS. TRUST ME.**
    #       Afterwards, go back to multithreading.
    # 
    # python3.7 signup.py -nelson 2 -swim 2 -dayofweek wed
    #       Suppose today is Saturday at 11:59pm. If I ran this, each thread will keep refreshing until wednesday becomes available,
    #       at which point all of them will immediately jump on a slot. This is how I usually book. Choose the NEXT day of the week that
    #       should logically appear in sequence.
    #
    # python3.7 signup.py -dayofweek wed -nelson 5 -swim 5 -stoponbook y
    #       Similarly, this runs 5 threads each, and then IF THERE IS A SUCCESSFUL BOOKING IN ONE OF THE THREADS (or you already booked
    #       something and you're running this again), all threads will stop once that's detected.
    ################ SUGGESTED USAGES ################

    
    ################ BENCHMARKS ################
    # PRE-REFRESH OPTIMIZATION (check for existing reservations every attempt)
    # Headless avg over 10 samples low traffic: 6.336627554893494
    # GUI avg over 10 samples low traffic: 6.923832178115845
    #
    # PRE-REFRESH OPTIMIZATION (no reservation check)
    # Headless avg over 10 samples low traffic: 4.0232669591903685
    # GUI avg over 10 samples low traffic: 4.428485107421875
    #
    # MULTITHREADING OPTIMIZATION
    # To be honest, once I implemented this, I have no idea how to benchmark this anymore -- the answer is: it will get you a slot.
    ################ BENCHMARKS ################

    # IMPORTANT: Read the #README before continuing, to make sure you setup your config properly.
    args = parse_args()

    # TODO: Cancel current reservation if a better reservation appears (so that ANY slot is grabbed and then replaced later...)
    # TODO: Add going through every day and find reservation for each day (if possible) -- this would prob be used overnight, rather than at midnight, to catch cancellations.
    # TODO: error check all selenium calls, cuz those get fucky if stuff is closed lol
    # TODO: add a delay option so if run overnight, it's not spamming -- it would check everything 30 seconds or so between attempts
    # TODO: stop threads on book?

    # Attempts to book a single day, according to the args passed in.
    multithread_book_single_day(args)
    # book_single_day(args)

if __name__ == "__main__":
    main()
#################### END MAIN ####################