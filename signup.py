#!/usr/bin/env python
import mechanicalsoup
import pickle
import selenium.webdriver
import time
import json
from datetime import date
from datetime import timedelta

CHROME_DRIVER_LOCATION = "./chromedriver"
COOKIE_PATH = "./cookies.json"
NELSON_BOOKING_URL = "https://bfit.brownrec.com/booking/4a42ba76-754b-48c9-95fd-8df6d4e3fb4d"
# TODO: add swimming support

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
    return (driver, date_options) # updated driver, if any

def load_chrome_and_dates():
    driver = try_load_chrome()
    return try_load_dates(driver)

def reset_cookies_load_chrome_and_dates(old_driver):
    if old_driver != None:
        old_driver.get(NELSON_BOOKING_URL)
    input("Login to your account, and then press any key.")
    save_cookie(old_driver, COOKIE_PATH)
    old_driver.close()
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
    book_btn.click()
    # Confirm whether or not we got the slot... 
    return successful_book(driver)

def select_reservation_date(date_options, days_from_now):
    reservation_date = date.today() + timedelta(days=days_from_now)
    reservation_date_by_name = reservation_date.strftime('%A')[:3] # BFit does names using first 3 letters
    if (reservation_date_by_name in date_options):
        date_options[reservation_date_by_name].click()

def try_book_for_day(driver, date_options, days_from_now):
    driver.refresh()
    (driver, date_options) = try_load_dates(driver)
    # TODO: Sort booking slots in order of priority -- that is, 
    # if I want [10 - 11AM, 2-3 PM], then I want to search booking_slots in that order.

    # for each day, loop through booking slots once.
    # put these in list, in order of priority as above
    # loop through this list when doing for slot in booking_slots
    
    # Make sure the correct day is selected visually 
    select_reservation_date(date_options, days_from_now)

    # Get all slots for that date
    booking_slots = driver.find_element_by_id("divBookingSlots").find_elements_by_class_name("booking-slot-item")

    # Attempt to book each slot
    for slot in booking_slots:
        book_btn = slot.find_element_by_tag_name("button")
        try:
            if not button_disabled(book_btn): # Make sure the slot is available...
                # Get the time slot for this specific button
                time_slot = slot.find_element_by_tag_name("p").text

                # Go through each timeslot you want, attempt to book
                if time_slot == "10 - 11 AM":
                    booked = try_book_slot(driver, book_btn)
                elif time_slot == "1:45 - 2:45 PM":
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

# Create an instance of chrome, add cookies, and refresh.
single_day_loop()