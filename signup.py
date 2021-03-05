#!/usr/bin/env python
import selenium.webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import json
import time
from datetime import date
from datetime import timedelta
from progress.bar import Bar
import argparse
import config

#################### START CONSTANTS ####################
SHIBBOLETH_USERNAME = config.username
SHIBBOLETH_PASSWORD = config.password
CHROME_DRIVER_LOCATION = "./chromedriver"
COOKIE_PATH = "./cookies.json"
NELSON_BOOKING_URL = "https://bfit.brownrec.com/booking/4a42ba76-754b-48c9-95fd-8df6d4e3fb4d"
SWIM_BOOKING_URL = "https://bfit.brownrec.com/booking/25de03fb-15e3-429d-bd3c-9483cc821ad5"
#################### END CONSTANTS ####################

#################### START HELPERS ####################
def parse_args():
    parser = argparse.ArgumentParser(description='Bfit Auto Booker')
    parser.add_argument('-book', help='which of [Nelson, Swim] you want to book', default='Nelson')
    parser.add_argument('-day', help='which day you want between [0, 3] where 0 is today, 3 is three days from now', default=3)
    parser.add_argument("-headless", help="enter y for no gui; enter n for gui.", default="n")
    # parser.add_argument('-all', help='path to output JSON', default=False) # TODO: add ability to go through all days...
    return parser.parse_args()

def try_accept_gdpr_cookie(driver):
    driver.find_element_by_id("gdpr-cookie-accept").click()

def check_for_reservation(driver): # TODO: optimize
    if (len(driver.find_elements_by_class_name("booking-slot-reserved-item")) > 0):
        return True
    return False

def try_load_chrome(chosen_url, is_headless):
    print("Loading Chrome...")
    # Create chrome instance & load cookies
    driver = create_driver_instance(chosen_url, is_headless)

    try:
        load_cookie(driver, COOKIE_PATH)
    except:
        return driver
    driver.refresh()

    # Try login
    try:
        driver.find_element_by_xpath('//button[normalize-space()="Brown Username"]').click()
    except: # no login button exists; probably caused by logining in and not restarting.
        driver.get(chosen_url) # try reloading the nelson booking!
    
    return driver

def get_date_options(driver):
    date_options = {}
    date_container = driver.find_elements_by_class_name("single-date-select-one-click")
    for datebtn in date_container:
        day_by_name = datebtn.find_element_by_class_name("single-date-select-button-day").get_attribute('innerHTML')
        date_options[day_by_name] = datebtn
    return date_options

def try_load_dates(chosen_url, driver, is_headless):
    # Dates for chrome
    print("Getting all dates for reservation page...")
    date_options = get_date_options(driver)
    if len(date_options) < 4: # always 4 dates at least #TODO: Add multiple attempts here, just in case it doesn't work on the first try (e.g., page fail to load during high traffic)
        (driver, date_options) = reset_cookies_load_chrome_and_dates(chosen_url, driver, is_headless)
    return (driver, date_options) # updated driver, if at all

def load_chrome_and_dates(chosen_url, is_headless):
    driver = try_load_chrome(chosen_url, is_headless)
    return try_load_dates(chosen_url, driver, is_headless)

def handle_shibboleth_login(driver):
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
    # save current page url
    current_url = driver.current_url

    print("Please login. Authenticate however you want!")

    # wait for URL to change with 30 seconds timeout
    WebDriverWait(driver, 30).until(EC.url_changes(current_url))

def create_headless_chrome(chosen_url):
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--enable-javascript')
    options.add_argument('--window-size=1920,1080')

    caps = DesiredCapabilities().CHROME
    # caps["pageLoadStrategy"] = "normal"  #  complete
    caps["pageLoadStrategy"] = "eager"  #  interactive
    driver = selenium.webdriver.Chrome(CHROME_DRIVER_LOCATION, options=options, desired_capabilities=caps)
    driver.implicitly_wait(10)
    driver.get(chosen_url)
    return driver

def create_chrome_with_gui(chosen_url):
    options = Options()
    options.add_argument('--enable-javascript')
    options.add_argument('--window-size=1920,1080')
    driver = selenium.webdriver.Chrome(CHROME_DRIVER_LOCATION, options=options)
    driver.implicitly_wait(10)
    driver.get(chosen_url)
    return driver

def create_driver_instance(chosen_url, is_headless):
    if (is_headless):
        return create_headless_chrome(chosen_url)
    return create_chrome_with_gui(chosen_url)

def reset_cookies_load_chrome_and_dates(chosen_url, old_driver, is_headless):
    old_driver.close()
    driver = create_driver_instance(chosen_url, False) # Always with GUI for auth purposes

    # Login
    handle_shibboleth_login(driver)

    # Save cookies after shibboleth
    # Accept cookies so the slot can actually be accepted lol
    try_accept_gdpr_cookie(driver)
    save_cookie(driver, COOKIE_PATH)
    driver.close()
    return load_chrome_and_dates(chosen_url, is_headless)

def button_disabled(element):
    # Last element should be "disabled"; optimized to only search last element.
    return "disabled" in element.get_attribute("class").split()[-1:]

def save_cookie(driver, path):
    with open(path, 'w') as filehandler:
        json.dump(driver.get_cookies(), filehandler)

def load_cookie(driver, path):
    with open(path, 'r') as cookiesfile:
        cookies = json.load(cookiesfile)
    for cookie in cookies:
        driver.add_cookie(cookie)

def print_driver_source_to_txt(driver, path):
    with open(path, 'w') as f1:
        f1.write(driver.page_source)

def successful_book(driver, book_btn):
    # TODO: different way of doing this for headless?
    return book_btn.get_attribute("disabled") != None # book button disables itself on a successful click.
    # return driver.find_element_by_id("alertBookingSuccess").get_attribute("hidden") == None # check to see if a success alert popped up

def try_book_slot(driver, book_btn):
    book_btn.click()
    # Confirm whether or not we got the slot... 
    return successful_book(driver, book_btn)

def select_reservation_date(date_options, days_from_now):
    print("Selecting reservation date...")
    reservation_date = date.today() + timedelta(days=days_from_now)
    reservation_date_by_name = reservation_date.strftime('%A')[:3] # BFit does names using first 3 letters
    if (reservation_date_by_name in date_options):
        refresh_reservation_date(date_options, reservation_date_by_name)
    # TODO: Make sure that the date inflection doesn't mess shit up... that is, if the target day doesn't exist yet, use the prev day.
    print("Reservation date selected:", reservation_date_by_name)
    return reservation_date_by_name

def refresh_reservation_date(date_options, reservation_date_by_name):
    # Optimized for Bfit -- clicking on a date refreshes buttons; no need to refresh whole page. Simply click on the correct date.
    # Make sure the correct day is selected visually 
    date_options[reservation_date_by_name].click()

def try_book_for_day(driver, date_options, reservation_date_by_name, ideal_times):
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
                        if (booked): # or slot.find_element_by_class_name("text-primary").text.strip().lower() == "booked"):
                            bar.finish()
                            return True
            bar.next()
        except: # probably caused by the booking being unsuccessful. Go to next slot.
            bar.next()
            continue
    bar.finish()
    return False # Didn't book this day :(

def book_single_day(chosen_url, days_from_now, is_headless):
    (driver, date_options) = load_chrome_and_dates(chosen_url, is_headless)

    # Make sure the correct date is chosen before beginning
    reservation_date_by_name = select_reservation_date(date_options, days_from_now)
    
    attempt_num = 0
    booked = False
    # booked = check_for_reservation(driver)
    # if (booked):
    #     print("You already have a valid reservation! Please cancel first before running this.")

    # Load the ideal time slots from the relevant config 
    ideal_times = []
    if (chosen_url == NELSON_BOOKING_URL):
        ideal_times = config.target_nelson_time_slots[reservation_date_by_name]
    else:
        ideal_times = config.target_swim_time_slots[reservation_date_by_name]
    
    while not booked: # while didn't book, keep trying!
        print("--------------")
        print("Starting attempt", attempt_num)
        booked = try_book_for_day(driver, date_options, reservation_date_by_name, ideal_times)
        if (booked): # or check_for_reservation(driver)
            print("Successfully grabbed slot :)")
            booked = True
        else:
            print("Attempt", attempt_num, "failed :(. Trying again.")
            attempt_num += 1
    
    # if (is_headless): # headless always should end program
    #     driver.close()
    #     return
    
    # input("...PRESS ANY KEY TO EXIT...")
    try:
        driver.close()
    except:
        print("Goodbye! (Although, you already closed me :(")

def book_single_day_benchmark(chosen_url, days_from_now, is_headless):
    sum = 0
    for i in range(10):
        t0 = time.time()
        book_single_day(chosen_url, days_from_now, is_headless)
        t1 = time.time()
        diff = t1-t0
        print(f"Total execution time for step {i}: {diff}")
        sum += diff
    print("avg:", sum/10)


#################### END HELPERS ####################
#################### MAIN ####################
def main():
    # EXAMPLE USAGES (assumes in gym_venv, activate via: source ~/gym_venv/bin/activate):
        # python3.7 signup.py -book swim -day 0
        # this would attempt to book swim slots for today.

        # python3.7 signup.py -book nelson -day 3
        # this would attempt to book nelson slots for 3 days from now
    

    ################ BENCHMARKS ################
    # PRE-REFRESH OPTIMIZATION (reservation check)
    # Headless avg over 10 samples low traffic: 6.336627554893494
    # GUI avg over 10 samples low traffic: 6.923832178115845
    #
    # PRE-REFRESH OPTIMIZATION (no reservation check)
    # Headless avg over 10 samples low traffic: 4.0232669591903685
    # GUI avg over 10 samples low traffic: 4.428485107421875
    ################ BENCHMARKS ################


    args = parse_args()
    chosen_url = ""
    if (args.book.lower() == "nelson"):
        chosen_url = NELSON_BOOKING_URL
    elif (args.book.lower() == "swim"):
        chosen_url = SWIM_BOOKING_URL
    
    # Create an instance of chrome, add cookies, and refresh.
    # TODO: Add ability to multithread & run multiple instances of this uwu!
    # TODO: add going through every day
    book_single_day(chosen_url, int(args.day), args.headless.lower() == "y")

if __name__ == "__main__":
    main()
#################### END MAIN ####################