#!/usr/bin/env python
import mechanize

br = mechanize.Browser()
br.set_handle_robots(False)

# Very important: this will fail if you haven't run the certifi script yet. Check the README.
br.open('https://bfit.brownrec.com/booking/4a42ba76-754b-48c9-95fd-8df6d4e3fb4d')
response = br.response()

print (response.geturl()) # URL of the page we just opened
print (response.info())   # headers
print (response.read())   # body