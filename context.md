WIFI SSID: ""
WIFI PASS: ""

Railway LINK: https://hub75pico-production-35d2.up.railway.app/distinct-keys
Github for railway app: https://github.com/jrrobers/hub_75_pico
(This folder connects to that github repo)

PICO to Waveshare Wiring: 
PIN_R1 = 2
PIN_G1 = 3
PIN_B1 = 6
PIN_R2 = 7
PIN_G2 = 8
PIN_B2 = 9
PIN_A = 10
PIN_CLK = 11
PIN_LAT = 12
PIN_OE = 13
PIN_D = 20
PIN_C = 18
PIN_B = 16

SETUP
Railway: I set up a service on railway which is deployed from this repo on github (using this folders main and requirements.). 
The railway app will do a couple simple things. 
- 1. It will count the distinct "organization" column in the table "access_keys" in my postgressql database
- 2. It will get the latest prices of stocks I list in main.py
- 3. It will pick a random quote from a quote bank located in the railway repo.

Then the pico should connect to wifi and display the scrolling. It will use circuitpy

Note:
    - there is a pico folder which houses the files to be loaded onto the pico in this folder for convenience. We will need to ensure the pico is in write mode, wipe the pico (I need help with this, not sure how), and load new code onto it which you will write in there. Make sure everything we need on the pico to display the text is present. 