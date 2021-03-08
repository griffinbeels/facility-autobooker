# Brown Facility Autobooker
Signup for Nelson / Swim gym slots automatically.


# Installation

### Assumptions:

* MacOS -- I developed this on Mac, not sure how it fares on Windows.
* Python3.7.3 -- I developed this using Python3.7.3, so if you use a different Python version, keep in mind that there *may* be issues.
* VSCode -- If I mention any IDE specific things, it will be in the context of VSCode.
* Git -- I will assume a basic understanding of Git and how to navigate directories.

# Getting Started

### Installation:

1. Clone this repo. If you don't have Git installed, [install it here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git). Clone by running the following in your terminal:
```
git clone https://github.com/griffinbeels/gym.git
```

2. `cd` into the cloned directory.

3. Create a virtual environment, by running the following in your terminal:
```
./create_venv.sh
```

4. If the virtual environment is not activated (make sure it's active every time you run this program), do so by entering:
```
source ~/gym_venv/bin/activate 
```

5. To run, simply enter (where arguments is a series of arguments defined in [Features](#Features)):
```
python3.7 signup.py [arguments]
```

### Configuration

After the initial installation above (MAKE SURE TO DO THAT), open the repo in your IDE of choice (in my case, VSCode). From there, open `sample_config.py`. This file informs `signup.py` about your preferred Nelson / Swim slots. Do the following:

1. Rename `sample_config.py` to `config.py` -- this will point `signup.py` to the correct file. **If you don't do this, the program will fail on `import config`**.

2. Open the newly renamed `config.py`. 

3. Replace `"username"` in `username = "username"` with the username you use to sign into Brown's SSO service (the page that loads when you click on Log In -> Brown Username on [this page](https://bfit.brownrec.com/)). This will allow the program to autofill your username when signing in.

3. Do the same for `"password"`. This will allow the program to autofill your password when signing in. **NOTE: this doesn't store your password anywhere, other than that config file you just edited -- don't worry!**.

4. Scroll down to `target_nelson_time_slots`. Enter the times for each day that you would like to register for.

    * Slots are split into sections based on their start time. For example, `start10am` defines the slot from `10 - 11 AM`. Logically, that slot starts at 10am, hence the variable name.

    * Examples are provided!

5. Scroll down to `target_swim_time_slots` and do the same as step 4. 

6. Run the program by choosing a series of arguments from [Features](#Features) down below, or referring to the [Examples](#Examples) section. Congrats, you did it!

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

# Examples

### **"I haven't run this yet tonight..."**
* Start the program by typing:
```
python3.7 signup.py -nelson 1
```
* This will load a single nelson slot attempt for 3 days from now. **More importantly, after you authenticate using Brown SSO, it will store your cookies!!!!** 

* Cookies are stored in `cookies.json` -- YOU NEED TO REFRESH THESE AT THE BEGINNING OF EVERY BOT SESSION. They expire pretty quick, so do this *right* before times are going to change for the night.

* This is incredibly important, and usually how I start using the program. This makes sure that, if I'm multithreading, I don't have to login to each thread -- they're all accessing some fresh, hot cookies.

### **"I loaded my cookies, and now I want to book a Nelson slot for this coming Thursday at midnight!!!!"**
* After loading your cookies using the above method, start the program around ~11:58 or so, by doing the following:

```
python3.7 signup.py -nelson 10 -dayofweek thu
```

* This will spin up 10 threads to start booking for you. You should see your terminal start to spam a lot of text. In particular, it will say `"Refreshing to get new reservation dates..."` until Thursday's slots are up.

* Keep this running until you book a slot!

### **"But I want both Nelson AND Swim slots to be booked :("**

* Do the same as the above, except with the following command:
```
python3.7 signup.py -nelson 5 -swim 5 -dayofweek thu
```

* Feel free to adjust the threads dedicated to each facility however you please.


# Conclusion

Try not to share this with too many people, as the efficacy of the bot diminishes as more people have access to good bots.
If you used this, and I didn't explicitly share it with you, that's fine, just make sure to buy me a beer or something the next time you see me! : ) 