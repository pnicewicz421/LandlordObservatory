import pandas as pd
from bs4 import BeautifulSoup
import mechanicalsoup
import regex
import requests
import urllib

from PyPDF2 import PdfFileReader
from io import BytesIO, StringIO

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from pdfminer.pdfpage import PDFPage
# this script goes into the URL of each violation and extracts all pertinent information, namely:
# notice number
# inspector_name
# inspector_number
# area_office_address
# area_office_city
# area_office_state
# area_office_zip
# violation_address
#--- violation_block
#--- violation_lot
# violation_issued_date
# violation_number
#--- number_of_items

##### specific_violation_codes

#--- PRIORITY ITEMS
##### LATER

def import_dhcd_data():
    # get dhcd file
    return pd.read_csv("all_violations.csv")

def parsePDF___OLD(url):
    # given url to pdf document, open pdf, convert to text, and output as string
    response = requests.get(url)

    with BytesIO(response.content) as open_pdf_file:
        read_pdf = PdfFileReader(open_pdf_file)
        num_pages = read_pdf.getNumPages()
        output = ""
        for p in range(num_pages):
            output += read_pdf.getPage(p).extractText()

    return output

def parsePDF(url):
    # given url to pdf document, open pdf, convert to text, and output as string
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    # Open the url provided as an argument to the function and read the content
    try:
        f = urllib.request.urlopen(urllib.request.Request(url)).read()
        # Cast to StringIO object
        fp = BytesIO(f)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()
        for page in PDFPage.get_pages(fp,
                                      pagenos,
                                    maxpages=maxpages,
                                    password=password,
                                    caching=caching,
                                      check_extractable=True):
            interpreter.process_page(page)
        fp.close()
        device.close()
        output = retstr.getvalue()
        retstr.close()
    except:
        output = ""
    return output

def readViolationData(url):
    # get pdf as text
    if type(url) != str:
        return "", ""
    print (url)
    output = parsePDF(url)
    
    #print (output)

    block_regex = r"(?<=Block:)([A-Z0-9]+)\s*(?=Lot:)"
    lot_regex = r"(?<=Lot:)([0-9]{3})"
    block = regex.findall(block_regex, output)
    lot = regex.findall(lot_regex, output)
    if len(block) == 0:
        block = ""
    else:
        block = block[0]
    if len(lot) == 0:
        lot = ""
    else:
        lot = lot[0]
    return block, lot


data = import_dhcd_data()
data[['Block', 'Lot']]  = data.apply(lambda row: readViolationData(row['See Notice']), axis=1, result_type='expand')
data.to_csv("violations_with_block_lot.csv", index=False)


