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
    'Sun': [start1230pm, start145pm],
    'Mon': [start5pm, start345pm],
    'Tue': [start115pm, start230pm],
    'Wed': [start5pm, start345pm],
    'Thu': [start115pm, start230pm, start345pm],
    'Fri': [start5pm, start345pm],
    'Sat': [start1230pm, start145pm]
}

# Time slots that you want for Swimming:
# SWIM:
# Monday - Friday:
start1015am = "10:15 - 11:15 AM"
start1130am = "11:30 AM - 12:30 PM"
start1245pm = "12:45 - 1:45 PM"

# Saturday & Sunday:
# start1245pm = "12:45 - 1:45 PM" # -- ALREADY DEFINED ABOVE
start2pm = "2 - 3 PM"

# IMPORTANT: Make sure the array is ordered by PREFERENCE (e.g., first item is most prefered slot)
target_swim_time_slots = {
    'Sun': [start1245pm, start2pm],
    'Mon': [start1245pm],
    'Tue': [start1245pm],
    'Wed': [start1245pm],
    'Thu': [start1245pm],
    'Fri': [start1245pm],
    'Sat': [start1245pm, start2pm]
}