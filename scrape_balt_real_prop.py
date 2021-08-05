# scrape balt_real prop

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import mechanicalsoup
import re, regex

def import_dhcd_data():
    # get dhcd file
    return pd.read_csv("violations_with_block_lot.csv")

def startForm(browser):
    # start page
    browser.open("https://cityservices.baltimorecity.gov/realproperty/default.aspx")    
    # select form
    form = browser.select_form('form[id="aspnetForm"]')
    form.choose_submit('ctl00$ctl00$rootMasterContent$LocalContentPlaceHolder$btnSearch')
    return browser, form

def retrieveOwnerData(html):
    # given html string, parse table and return these variables:
    # block, lot, property_address, owner, owner_street_address, owner_city, owner_state, owner_zip
    response = browser.submit_selected()
    html = response.text

    soup = BeautifulSoup(html)

    # find number of records
    num_records = soup.find("span", {"id": "ctl00_ctl00_rootMasterContent_LocalContentPlaceHolder_lblStatus"})
    if num_records is None:
        # couldn't retrieve any records
        num_records = 0
    else:
        # get number of records as int
        num_records = int(re.sub("[^0-9]", "", num_records.get_text()))

    if num_records == 1:
        # get table
        table = soup.find("table", {"class": "dataTable"})
        owner_data = pd.read_html(str(table), header=0)[0]

        owner_last_name = owner_data.Owner.apply(lambda row: regex.findall('^(.+?),', row)[0])
        owner_first_name = owner_data.Owner.apply(lambda row: regex.findall(',\s([A-Za-z\s]+)', row)[0])
        owner_street_address = owner_data.Owner.apply(lambda row: regex.findall('([0-9A-Z]+)', row)[0])

    return num_records
    # soup.select_one("ctl00_ctl00_rootMasterContent_LocalContentPlaceHolder_lblStatus").text)

    #"ctl00_ctl00_rootMasterContent_LocalContentPlaceHolder_lblStatus"

def retrieveOwner(browser):


    # find number of records first
    result = re.sub("[^0-9]", "", str(retrieveOwnerData(response.text)))
    print(address, fiscal_year, result)


def findOwner(block, lot, address, fiscal_year, browser):
    global available_fiscal_years

    # select year - if available fiscal yeaar
    if str(fiscal_year) not in available_fiscal_years:
        print("bad fiscal year")
        return ""

    form.set_select({"ctl00$ctl00$rootMasterContent$LocalContentPlaceHolder$ddYears": fiscal_year})

    # try block/lot first. if empty, try address
    if block is not np.nan and lot is not np.nan:
        form["ctl00$ctl00$rootMasterContent$LocalContentPlaceHolder$txtBlock"] = block
        form["ctl00$ctl00$rootMasterContent$LocalContentPlaceHolder$txtLot"] = lot
        response = retrieveOwner(browser)
        
        



    form["ctl00$ctl00$rootMasterContent$LocalContentPlaceHolder$txtAddress"] = address
    response = browser.submit_selected()




    #block, lot, property_address, owner, owner_street_address, owner_city, owner_state, owner_zip = retrieveOwnerData(response.text)

    browser, form = startForm(browser)
    
    return result

data = import_dhcd_data()
browser = mechanicalsoup.StatefulBrowser()
browser, form = startForm(browser)

# convert notice date to datetime
data['Date Notice'] = pd.to_datetime(data['Date Notice'])

# create fiscal year column based on notice date
data['Fiscal Year'] = data['Date Notice'].apply(lambda row: row.year if row.month < 7 else row.year + 1)

# change lot to string with 3 characters (since python forced it to float) 
data['Lot'] = data['Lot'].fillna(0).astype(int)
data['Lot'] = data['Lot'].astype('str').str.zfill(3)
data.loc[data['Lot']=='000','Lot'] = np.nan

# get select tag for fiscal year dropdown
select = browser.page.find(id="ctl00_ctl00_rootMasterContent_LocalContentPlaceHolder_ddYears")

# get all available fiscal years
available_fiscal_years=[]
options = select.find_all("option")
for o in options:
    available_fiscal_years.append(o.get("value"))

# remove the earliest one due to some bug on the website causing it not to appear on the form
available_fiscal_years.pop()

# apply FindOwner function to each row
data['num_records'] = data.apply(lambda row: findOwner(row['Block'], row['Lot'], row['Address'], row['Fiscal Year'], browser), axis=1)