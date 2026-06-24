# Advertpreneur - Amazon.de Scraper
# Setup and Run Instructions
# ================================================

## ONE-TIME SETUP (run these once only)

Step 1 - Open a terminal / command prompt in this folder

Step 2 - Install Python dependencies:
    pip install flask playwright

Step 3 - Install Playwright browsers:
    playwright install chromium

That is it. Setup done.

## RUNNING THE SCRAPER

Every time you want to use it:

    python app.py

Then open your browser and go to:
    http://localhost:5000

## HOW TO USE

1. Type your keyword in the search box (e.g. "tote bags")
2. Select how many pages to scrape (1 to 5)
3. Click Start Scraping
4. A visible browser window will open and scrape automatically
5. Results appear in the dashboard in real time
6. Click Download CSV when done

## COLUMN D - Service values for the email script
    Amazon SEO
    Listing Images
    PPC
    A+ Content

## NOTES

- Berlin ZIP 10115 is set automatically
- Sellers sold by Amazon are skipped automatically
- Sponsored and Organic listings are both captured and tagged
- CSV exports to the /exports folder inside this directory
- Keep the terminal window open while using the scraper
- Do not close the browser window that opens automatically

## FOLDER STRUCTURE

    amazon_de_scraper/
    |-- app.py           Main server (run this)
    |-- scraper.py       Playwright scraping logic
    |-- requirements.txt Dependencies
    |-- templates/
    |   |-- index.html   Dashboard UI
    |-- exports/         CSV files saved here
