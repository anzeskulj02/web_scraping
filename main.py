import gspread
import requests
from bs4 import BeautifulSoup
import time
from datetime import date
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

search = [[], []]


def trustpilot_ratings():
    ratings = {}
    for casino_name in search[0]:
        page = requests.get("https://www.trustpilot.com/review/" + casino_name)  # scrape web site
        if page.status_code != 200:  # if page don't exist (no review made for this casino)
            ratings[casino_name] = "/"
            continue
        soup = BeautifulSoup(page.content, 'html.parser')

        data = soup.find_all(attrs={"data-rating-typography": "true"})
        if data[0].text != 0:
            ratings[casino_name] = data[0].text
        else:
            ratings[casino_name] = "/"
        time.sleep(0.5)  # wait 0.5 seconds than procced to nex review
        continue
    return ratings


def askgamblers_rating():
    ratings = {}

    options = Options()
    options.headless = False
    options.add_argument("--window-size=720,1280")  # fake screen size to fool web server from recognizing bot.
    DRIVER_PATH = 'PATH/chromedriver.exe'  # path to chromedriver.exe. Need to be downloaded from official web page "https://sites.google.com/chromium.org/driver/"

    for casino_name in search[1]:
        driver = webdriver.Chrome(options=options, executable_path=DRIVER_PATH)  # init of driver
        driver.minimize_window()
        driver.get(
            'https://www.askgamblers.com/quick-search/casinos?q=' + str(casino_name))  # search for casino by name
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        data = soup.find_all(class_="star-rating-num")

        if len(data) == 0:  # check if data is empty (No results found when searching
            ratings[casino_name] = "/"
        else:
            ratings[casino_name] = data[0].text
        time.sleep(1)  # wait for a second to fool web server
        driver.quit()  # close the driver
    return ratings


def write_in_db(worksheet, name, data):
    row_counter = 2
    cell = worksheet.findall(name)
    column = cell[0].col
    for i in data:
        worksheet.update_cell(row_counter, column, data[i])
        row_counter += 1
        time.sleep(0.1)


def run():
    # connect to spreadsheet
    gc = gspread.service_account(filename='scraping-334315-9de84acb270e.json')
    sh = gc.open("Scraped Reviews Data")
    worksheet = sh.get_worksheet(0)

    # get all casinos from spreadsheet
    list_of_dicts = worksheet.get_all_records()

    # for trustpilot ratings get url's of casino, for askgabliners ratings use casino's name
    for i in list_of_dicts:
        search[0].append(i['URL'].partition('//')[2])  # remove https://
        search[1].append(i['CASINO NAME'])

    x = trustpilot_ratings()
    write_in_db(worksheet, "TRUSTPILOT RATING", x)

    y = askgamblers_rating()
    write_in_db(worksheet, "ASKGAMBLERS RATING", y)

    write_in_db(worksheet, "LAST SCRAPING TIME", {'time': date.today().strftime("%d/%m/%Y")})  # update last scraping time


run()