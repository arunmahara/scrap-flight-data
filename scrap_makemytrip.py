import time
import datetime
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# User defined variables for data retrieval
depart = '10/03/2023'
from_airport_code = 'DEL'
to_aiport_code  = 'BOM'
adults = 1
children = 0
infants = 0
cabin_class = 'E'  #choices = 'E', 'PE, 'B', 'F

baseUrl = f'https://www.makemytrip.com/flight/search?itinerary={from_airport_code}-{to_aiport_code}-{depart}&tripType=O&paxType=A-{adults}_C-{children}_I-{infants}&intl=false&cabinClass={cabin_class}'

try:
    driver = webdriver.Chrome(executable_path="./chromedriver")

    print ("Requesting URL")
    driver.get(baseUrl) 
    print ("Webpage found ...")

    # Wait until the first box with relevant flight data appears on Screen
    element = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="left-side--wrapper"]/div[2]')))

    # Scroll the page till bottom to get full data available in the DOM.
    print ("Scrolling document upto bottom ...")
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, arguments[0]);", last_height)

        # Wait to load page
        time.sleep(2)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.documentElement.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height

    # Find the document body and get its inner HTML for processing in BeautifulSoup parser.
    body = driver.find_element(By.TAG_NAME,"body").get_attribute("innerHTML")

    print("Closing Chrome ...")
    driver.quit() 			

    print("Getting data from DOM ...")
    soupBody = BeautifulSoup(body, features="html.parser") # Parse the inner HTML using BeautifulSoup

    # Extract the required tags 
    __flight_name = soupBody.find_all("p", "boldFont blackText airlineName") 
    __flight_code = soupBody.find_all("p",  "fliCode")			
    __flight_duration = soupBody.find_all("div", "stop-info flexOne")	
    __flight_cost = soupBody.find_all("p", "blackText fontSize18 blackFont white-space-no-wrap")
    __flight_departure = soupBody.find_all('div', "flexOne timeInfoLeft")
    __flight_arrival = soupBody.find_all('div', "flexOne timeInfoRight")


    # list comprehension to get all flight details accordingly 
    print("Extracting flight details ...")
    depart_date =  datetime.datetime.strptime(depart, "%d/%m/%Y").strftime("%a, %b %d, %Y")
    columns = ['depart', 'airline', 'flight-code', 'departure-time', 'departure-city', 'flight-duration', 'flight-layover', 'arrival-time', 'arrival-city', 'flight-cost']
    flights = [
        {
            columns[0]: depart_date,                                # departure date 
            columns[1]: name.text,                                  # flight name 
            columns[2]: code.text,                                  # flight code 
            columns[3]: dep.find('span').text,                      # flight departure time
            columns[4]: dep.find('font').text,                      # flight departure city
            columns[5]: dur.find("p").text,                         # flight duration
            columns[6]: dur.find("p", "flightsLayoverInfo").text,   # flight layover (connecting flight)
            columns[7]: arv.find('span').text,                      # flight arrival time
            columns[8]: arv.find('font').text,                      # flight arrival city
            columns[9]: cost.text,                                  # flight cost
        } 
        for name, code, dep, dur, arv, cost in zip(__flight_name, __flight_code, __flight_departure, __flight_duration, __flight_arrival, __flight_cost)
    ]

    print("Creating csv file ...")
    df = pd.DataFrame(flights, columns=columns)
    df.index += 1 
    df.to_csv('flight_details.csv', index_label='SN')
    print("Scrapping Completed!!!")
    
except Exception as e:
	print (str(e))
