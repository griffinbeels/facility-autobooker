#!/usr/bin/env python
import selenium.webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from datetime import date
from datetime import timedelta
import config

#################### START CONSTANTS ####################
SHIBBOLETH_USERNAME = config.username
SHIBBOLETH_PASSWORD = config.password
CHROME_DRIVER_LOCATION = "./chromedriver"
COOKIE_PATH = "./cookies.json"
NELSON_BOOKING_URL = "https://bfit.brownrec.com/booking/4a42ba76-754b-48c9-95fd-8df6d4e3fb4d"
# TODO: add swimming support
#################### END CONSTANTS ####################

#################### START HELPERS ####################
def try_load_chrome():
    # Create chrome instance & load cookies
    driver = selenium.webdriver.Chrome(CHROME_DRIVER_LOCATION)
    driver.get(NELSON_BOOKING_URL)
    try:
        load_cookie(driver, COOKIE_PATH)
    except:
        return driver
    driver.refresh()
    driver.implicitly_wait(2)

    # Try login
    try:
        driver.find_element_by_xpath('//button[normalize-space()="Brown Username"]').click()
    except: # no login button exists; probably caused by logining in and not restarting.
        driver.get(NELSON_BOOKING_URL) # try reloading the nelson booking!
    
    return driver

def get_date_options(driver):
    date_options = {}
    date_container = driver.find_elements_by_class_name("single-date-select-one-click")
    for datebtn in date_container:
        day_by_name = datebtn.find_element_by_class_name("single-date-select-button-day").text
        date_options[day_by_name] = datebtn
    return date_options

def try_load_dates(driver):
    # Dates for chrome
    date_options = get_date_options(driver)
    if len(date_options) == 0:
        (driver, date_options) = reset_cookies_load_chrome_and_dates(driver)
    return (driver, date_options) # updated driver, if at all

def load_chrome_and_dates():
    driver = try_load_chrome()
    return try_load_dates(driver)

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

    # wait for URL to change with 15 seconds timeout
    WebDriverWait(driver, 30).until(EC.url_changes(current_url))

def reset_cookies_load_chrome_and_dates(old_driver):
    old_driver.close()
    driver = selenium.webdriver.Chrome(CHROME_DRIVER_LOCATION)
    driver.implicitly_wait(2)
    driver.get(NELSON_BOOKING_URL)

    # Login
    handle_shibboleth_login(driver)

    # Save cookies after shibboleth
    save_cookie(driver, COOKIE_PATH)
    driver.close()
    return load_chrome_and_dates()

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

def successful_book(driver):
    return driver.find_element_by_id("alertBookingSuccess").get_attribute("hidden") == None

def try_book_slot(driver, book_btn):
    # book_btn.click()
    # Confirm whether or not we got the slot... 
    return successful_book(driver)

def select_reservation_date(date_options, days_from_now):
    reservation_date = date.today() + timedelta(days=days_from_now)
    reservation_date_by_name = reservation_date.strftime('%A')[:3] # BFit does names using first 3 letters
    if (reservation_date_by_name in date_options):
        date_options[reservation_date_by_name].click()
    return reservation_date_by_name

def try_book_for_day(driver, date_options, days_from_now):
    driver.refresh()
    (driver, date_options) = try_load_dates(driver)
    # TODO: Sort booking slots in order of priority -- that is, 
    # if I want [10 - 11AM, 2-3 PM], then I want to search booking_slots in that order.

    # for each day, loop through booking slots once.
    # put these in list, in order of priority as above
    # loop through this list when doing for slot in booking_slots
    
    # Make sure the correct day is selected visually 
    reservation_date_by_name = select_reservation_date(date_options, days_from_now)

    # Get all slots for that date
    booking_slots = driver.find_element_by_id("divBookingSlots").find_elements_by_class_name("booking-slot-item")

    # Attempt to book each slot
    for slot in booking_slots:
        book_btn = slot.find_element_by_tag_name("button")
        try:
            if button_disabled(book_btn): # Make sure the slot is available...
                # Get the time slot for this specific button
                time_slot = slot.find_element_by_tag_name("p").text

                # Go through all timeslots for the reservation day, attempt to book
                for target_time_slot in config.target_time_slots[reservation_date_by_name]:
                    print("attempting to book", reservation_date_by_name, "at", target_time_slot)
                    if time_slot == target_time_slot:
                        booked = try_book_slot(driver, book_btn)
                    # Return if booked successfully
                    if (booked):
                        return True 
        except: # probably caused by the booking being unsuccessful. Go to next slot.
            continue
    return False # Didn't book this day :(

def single_day_loop():
    (driver, date_options) = load_chrome_and_dates()

    attempt_num = 0
    booked = False
    while not booked: # while didn't book, keep trying!
        booked = try_book_for_day(driver, date_options, 3)
        print("attempt", attempt_num, "failed :(. Trying again.")
        attempt_num += 1
    
    input("press any key to quit")
    driver.close()

    # TODO: Go through each day, starting from most recent, and if there is an open slot that matches preference, try to book.

#################### END HELPERS ####################

#################### MAIN ####################
def main():
    # Create an instance of chrome, add cookies, and refresh.
    single_day_loop()

if __name__ == "__main__":
    main()
#################### END MAIN ####################