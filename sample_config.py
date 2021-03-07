username = "username" # Username for SSO login
password = "password" # Password for SSO login

# NEXT: Fill out your ideal timeslots for each day.
# Make sure they're in the EXACT format as seen on the site (or as depicted below).

# Time slots that you want for the Nelson:
# NELSON:
# Monday - Friday:
start730am = "7:30 - 8:30 AM"
start845am = "8:45 - 9:45 AM"
start10am = "10 - 11 AM"
start1115am = "11:15 AM - 12:15 PM"
start115pm = "1:15 - 2:15 PM"
start230pm = "2:30 - 3:30 PM"
start345pm = "3:45 - 4:45 PM"
start5pm = "5 - 6 PM"

# Saturday & Sunday:
# start10am = "10 - 11 AM" # -- ALREADY DEFINED ABOVE
# start1115am = "11:15 AM - 12:15 PM" # -- ALREADY DEFINED ABOVE
start1230pm = "12:30 - 1:30 PM"
start145pm = "1:45 - 2:45 PM"

# IMPORTANT: Make sure the array is ordered by PREFERENCE (e.g., first item is most prefered slot)
target_nelson_time_slots = {
    'sun': [start1230pm, start145pm],
    'mon': [start5pm, start345pm],
    'tue': [start115pm, start230pm],
    'wed': [start5pm, start345pm],
    'thu': [start115pm, start230pm, start345pm],
    'fri': [start5pm, start345pm],
    'sat': [start1230pm, start145pm]
}

# Time slots that you want for Swimming:
# SWIM:
# Monday - Friday:
start9am = "9 - 10 AM"
start1015am = "10:15 - 11:15 AM"
start1130am = "11:30 AM - 12:30 PM"
start1245pm = "12:45 - 1:45 PM"

# Saturday & Sunday:
# start1245pm = "12:45 - 1:45 PM" # -- ALREADY DEFINED ABOVE
start2pm = "2 - 3 PM"

# IMPORTANT: Make sure the array is ordered by PREFERENCE (e.g., first item is most prefered slot)
target_swim_time_slots = {
    'sun': [start1245pm, start2pm],
    'mon': [start9am],
    'tue': [start1245pm],
    'wed': [start1245pm],
    'thu': [start1245pm],
    'fri': [start1245pm],
    'sat': [start1245pm, start2pm]
}