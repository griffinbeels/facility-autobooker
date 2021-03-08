# Brown Facility Autobooker
Signup for Nelson / Swim gym slots automatically.


# Installation

### Assumptions:

* MacOS -- I developed this on Mac, not sure how it fares on Windows.
* Python3.7.3 -- I developed this using Python3.7.3, so if you use a different Python version, keep in mind that there *may* be issues.


### Intructions:

1. Create a virtual environment, by running the following in your terminal:
```
./create_venv.sh
```

2. If the virtual environment is not activated, do so by entering:
```
source ~/gym_venv/bin/activate 
```

3. To run, simply enter:
```
python3.7 signup.py [arguments]
```

# Getting Started

### Configuration

The 

# Features

Note: this program is multithreaded, so many arguments correspond to mulitithreaded functionality.

### Arguments
You can find all of the arguments at the top of signup.py, however here are all of them defined:

1. `-nelson [num_threads]` [must have at least one Nelson thread or one Swim thread]

    * **Definition:** Defines the number of threads to dedicate to booking a Nelson slot.

    * **Valid Values:** 0 (no Nelson threads) to infinity (however many your computer can handle)

    * **Notes:** I personally don't see a need past like 10 threads, so I wouldn't recommend going above 10 -- but knock yourself (and your computer) out if you want.

    * **Usage:** `python3.7 signup.py -nelson 1`

        * This gives you a single thread dedicated for nelson booking.
    
    * **Default:** `0`.

2. `-swim [num_threads]` [must have at least one Nelson thread or one Swim thread]

    * **Definition:** Defines the number of threads to dedicate to booking a Swim slot.

    * **Valid Values:** 0 (no Swim threads) to infinity (however many your computer can handle)

    * **Notes:** See above.

    * **Usage:** `python3.7 signup.py -swim 2 -nelson 1`

        * This gives you a single thread dedicated for nelson booking AND 2 for swim bookings. Yes, you can do both at the same time!
    
    * **Default:** `0`.

3. `-daysfromnow [days_from_now]` [optional]

    * **Definition:** Indicates the day you want to book for by how many days away it is from today (e.g., if today is Monday, and we want Wednesday, the `days_from_now` is 2.)

    * **Valid Values:** 0 (today) to 3 (max distance from today, based on current Bfit rules).

    * **Notes:** Usually I don't use this. Instead I use `-dayofweek`, see the notes for that argument.

    * **Usage:** `python3.7 signup.py -swim 2 -nelson 1 -dayofweek 0`

        * Just like the example in `-swim`, except it books for today!
    
    * **Default:** `3`

4. `-dayofweek [day_by_name]` [optional]

    * **Definition:** Indicates the day you want to book for by the name of the day.

    * **Valid Values:** Any of `["sun", "mon", "tue", "wed", "thu", "fri", "sat"]`. This is because Bfit stores dates by the first three letters.

    * **Notes:** I usually use this argument. This is because when the time goes from 11:59 on one day to midnight on the next day, the notion of `days_from_now` is messed up. However, searching by day of the week by name means that you can start the script at 11:59pm, and it still makes sense for the duration of the program. You're always booking for, say, "wed" rather than "3 days from now" which changes.

    * **Usage:** `python3.7 signup.py -swim 2 -nelson 1 -dayofweek mon`

        * Just like the example in `-swim`, except it books for Monday explicitly.
    
    * **Default:** `None` -- this means it will default to `-daysfromnow`.

5. `-headless [y_or_n]` [optional]

    * **Definition:** Indicates whether or not the program should run headless (without a GUI).

    * **Valid Values:** One of `{y, n}`. `y` indicates you DON'T want a GUI; `n` indicates you want a GUI.

    * **Notes:** I usually use this argument set to `y`. This is because I found gains with running in headless mode, especially with multiple threads.

    * **Usage:** `python3.7 signup.py -swim 2 -nelson 1 -dayofweek mon -headless y`

        * Just like the example in `-dayofweek`, except explicitly indicating no GUI.
    
    * **Default:** `y`.

6. `-stoponbook [y_or_n]` [optional]

    * **Definition:** Indicates whether or not all threads should stop once a successful booking (or prior reservation) is found by a different thread.

    * **Valid Values:** One of `{y, n}`. `y` indicates you want all threads to stop; `n` indicates you want all threads to continue.

    * **Notes:** This ONLY STOPS THREADS OF THE SAME TYPE; that is, finding a Nelson slot DOES NOT stop the Swim threads from searching. I usually use `y` just because I think it's fun to see it stop when it works!

    * **Usage:** `python3.7 signup.py -swim 2 -nelson 1 -dayofweek mon -headless y -stoponbook y`

        * Just like the example in `-headless`, except explicitly indicating that we want to stop upon booking.
    
    * **Default:** `y`.

