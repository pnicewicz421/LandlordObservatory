# Landlord Observatory

This is the working code to an visualization-based tool to identify landlords in Baltimore, MD that have had repeated housing violations against them cited by Baltimore Housing and Community Development. 

## Cleaning

This begins by scraping all violation housing violation data. scrape_dhcd.py extracts violations while get_violation_details.py begins to scrape underlying violation data in the notices stored as pdfs.

    scrape_dhcd.py
    get_violation_details.py

Next, we scrape and extract the owners names and information from the Baltimore Tax & Assessment page for each violation location.

    scrape_balt_real_prop.py

    
#### To be continued!
        
