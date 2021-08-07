# scrape balt_real prop

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import mechanicalsoup
import xml
import re, regex

global browser, form

def import_dhcd_data():
    # get dhcd file
    return pd.read_csv("violations_with_block_lot.csv")

def startForm():
    global browser, form
    # start page
    browser.open("https://cityservices.baltimorecity.gov/realproperty/default.aspx")    
    # select form
    form = browser.select_form('form[id="aspnetForm"]')
    form.choose_submit('ctl00$ctl00$rootMasterContent$LocalContentPlaceHolder$btnSearch')


def retrieveOwnerData():
    # given html string, parse table and return these variables:
    # block, lot, property_address, owner, owner_street_address, owner_city, owner_state, owner_zip
    global browser, form
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

    owner1 = soup.find("span", {"id": "ctl00_ctl00_rootMasterContent_LocalContentPlaceHolder_DataGrid1_ctl02_lblOwner1"}).text.strip()
    owner2 = soup.find("span", {"id": "ctl00_ctl00_rootMasterContent_LocalContentPlaceHolder_DataGrid1_ctl02_lblOwner2"}).text.strip()
    owner3 = soup.find("span", {"id": "ctl00_ctl00_rootMasterContent_LocalContentPlaceHolder_DataGrid1_ctl02_lblOwner3"}).text.strip()
    owner4 = soup.find("span", {"id": "ctl00_ctl00_rootMasterContent_LocalContentPlaceHolder_DataGrid1_ctl02_lblOwner4"}).text.strip()

    # pattern for identifying if multiple owners exist:
    if owner4 == '':
        # one owner
        owner1_name = owner1 
        owner2_name = ""
        owner_street_address = owner2
        owner_city_state = owner3
    else:
        owner1_name = owner1 
        owner2_name = owner2
        owner_street_address = owner3
        owner_city_state = owner4

    # pattern for identifying whether owner is a corporation 
    corporation1 = regex.findall('((?:LIMITED)?\s?(?:PARTNERSHIP)?)$|(LL(?:L)?(C|P)(?:\.)?$|INC(?:\.)?(?:ORPORATED)?(?:,)?(?:\s+THE)?)$|(TRUST)$|(REALTY)$|(CORP(?:\.)?(?:,)?(?:ORATION)?(?:.)?(?:\s+THE)?)$', owner1_name)
    corporation2 = regex.findall('((?:LIMITED)?\s?(?:PARTNERSHIP)?)$|(LL(?:L)?(C|P)(?:\.)?$|INC(?:\.)?(?:ORPORATED)?(?:,)?(?:\s+THE)?)$|(TRUST)$|(REALTY)$|(CORP(?:\.)?(?:,)?(?:ORATION)?(?:.)?(?:\s+THE)?)$', owner2_name)
    
    print(corporation1) 
    print(corporation2)   
    
    if len(corporation1) > 0:
        is_corporation1 = True
    else:
        is_corporation1 = False
        

    if len(corporation2) > 0:
        is_corporation2 = True
    else:
        is_corporation2 = False

    return [owner1_name, owner2_name, owner_street_address, owner_city_state, is_corporation1, is_corporation2]
    # soup.select_one("ctl00_ctl00_rootMasterContent_LocalContentPlaceHolder_lblStatus").text)

    #"ctl00_ctl00_rootMasterContent_LocalContentPlaceHolder_lblStatus"


def findOwner(block, lot, address, fiscal_year):
    global available_fiscal_years, browser, form

    # select year - if available fiscal yeaar
    if str(fiscal_year) not in available_fiscal_years:
        return [None]*6

    form.set_select({"ctl00$ctl00$rootMasterContent$LocalContentPlaceHolder$ddYears": fiscal_year})
    # try block/lot first. if empty, try address
    if block is not np.nan and lot is not np.nan:
        form["ctl00$ctl00$rootMasterContent$LocalContentPlaceHolder$txtBlock"] = block
        form["ctl00$ctl00$rootMasterContent$LocalContentPlaceHolder$txtLot"] = lot
        result = retrieveOwnerData()
    else:
        form["ctl00$ctl00$rootMasterContent$LocalContentPlaceHolder$txtAddress"] = address
    #result = browser.submit_selected()

    #block, lot, property_address, owner, owner_street_address, owner_city, owner_state, owner_zip = retrieveOwnerData(response.text)

    startForm()
    
    return result

data = import_dhcd_data()
browser = mechanicalsoup.StatefulBrowser()
startForm()

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
data[['owner1_name', 'owner2_name', 'owner_street_addrress', 'owner_city_state', 'is_corporation1', 'is_corporation2']] = data.apply(lambda row: findOwner(row['Block'], row['Lot'], row['Address'], row['Fiscal Year']), axis=1, result_type='reduce')
data = data.apply(lambda row: findOwner(row['Block'], row['Lot'], row['Address'], row['Fiscal Year']), axis=1, result_type='expand')


### dev prep for owner functions
i = 2
block=data.iloc[i,-3]
lot=data.iloc[i,-2]
address=data.iloc[i,0]
fiscal_year=data.iloc[i,-1]