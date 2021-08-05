# DCHD data

#import requests
from bs4 import BeautifulSoup
import mechanicalsoup
import re

import pandas as pd

domain = 'http://cels.baltimorehousing.org'

def startForm(browser):
    # navigate to page
    browser.open(domain + "/Search_On_Map.aspx")
    # select form
    form = browser.select_form('form[id="aspnetForm"]')
    # check 'By Neighborhood'
    form.set_checkbox({"ctl00$ContentPlaceHolder1$ck2": True})
    return browser, form

def getData(html):
    # given html string, parse table and return dataframe
    soup = BeautifulSoup(html)
    # get table
    table = soup.find("table", {"class": "datagrid"})
    # if no records found (no table), return empty dataframe 
    if table == None:
        return pd.DataFrame()
    # strip extra html tags in url for notices for proper rendering
    str_table = re.sub('<a href="\.\.(.+?)" target="_blank"><img alt="Notice" border="0" src="images/PDF.jpg"/></a>', domain + '\\1', str(table))
    table = BeautifulSoup(str_table)
    # convert to dataframe and return
    df = pd.read_html(str(table), header=0)[0]
    return df

browser = mechanicalsoup.StatefulBrowser()

browser, form = startForm(browser)

# get select tag for neighborhoods
neighborhood_select = browser.page.find(id="ctl00_ContentPlaceHolder1_lstLoc")

# get all possible neighborhood options
options = neighborhood_select.find_all("option")

# store all output in master dataframe
master_df = []

for o in options:
    value = o.get("value")
    if value.strip()=="":
        # skip if neighborhood value empty 
        continue

    # select value
    form.set_select({"ctl00$ContentPlaceHolder1$lstLoc": value})

    # collect response and store in variable html
    response = browser.submit_selected()
    html = response.text

    # parse html and store in dataframe
    result_df = getData(html)
   
    # add to master_df
    master_df.append(result_df) 
  
    print ("Finished processing " + value)

    # reset browser to previous state
    browser, form = startForm(browser)

result = pd.concat(master_df)
result.to_csv("all_violations.csv", index=False)