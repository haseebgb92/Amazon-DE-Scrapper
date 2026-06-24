# Amazon.de Scraper

Professional Amazon Germany seller discovery and lead generation tool built with Flask and Playwright.

**Developed by Muhammad Haseeb**
Founder, Advertpreneur

---

## Overview

Amazon.de Scraper automates the collection of seller information from Amazon Germany search results. The application captures both Sponsored and Organic listings, filters out Amazon-owned products, and exports qualified seller data into CSV format for outreach, lead generation, competitor research, and Amazon service prospecting.

---

## Features

* Real-time scraping dashboard
* Amazon Germany marketplace support
* Organic and Sponsored listing detection
* Automatic Amazon-owned seller filtering
* Live progress updates
* CSV export functionality
* Multi-page scraping (1–5 pages)
* Automated browser interaction using Playwright
* Service categorization for outreach campaigns

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/haseebgb92/Amazon-DE-Scrapper.git
cd Amazon-DE-Scrapper
```

### 2. Install Dependencies

```bash
pip install flask playwright
```

### 3. Install Chromium Browser

```bash
playwright install chromium
```

Setup is now complete.

---

## Running the Application

Start the application using:

```bash
python app.py
```

Open your browser and navigate to:

```text
http://localhost:5000
```

---

## How to Use

### Step 1

Enter an Amazon Germany keyword.

Examples:

* tote bags
* yoga mat
* kitchen organizer
* water bottle

### Step 2

Select the number of pages to scrape.

Supported range:

* 1 Page
* 2 Pages
* 3 Pages
* 4 Pages
* 5 Pages

### Step 3

Click **Start Scraping**.

The scraper will automatically launch a browser window and begin collecting seller data.

### Step 4

Monitor results in real time through the dashboard.

### Step 5

Once complete, download the results using the **Download CSV** button.

---

## Exported Data

The scraper exports seller information into CSV format for further processing and outreach.

Service categories include:

* Amazon SEO
* Listing Images
* PPC Management
* A+ Content

---

## Important Notes

* Berlin ZIP Code **10115** is automatically applied.
* Amazon Retail listings are excluded.
* Sponsored listings are tagged separately.
* Organic listings are tagged separately.
* CSV exports are saved in the `exports` directory.
* Keep the terminal running while scraping.
* Do not manually close the browser window opened by Playwright.

---

## Project Structure

```text
amazon_de_scraper/
│
├── app.py
├── scraper.py
├── requirements.txt
│
├── templates/
│   └── index.html
│
├── exports/
│   └── *.csv
│
└── README.md
```

---

## Technology Stack

* Python
* Flask
* Playwright
* Chromium
* HTML
* CSS
* JavaScript

---

## Author

### Muhammad Haseeb

Founder & Lead Developer, Advertpreneur

Expertise:

* Amazon SEO
* Amazon PPC
* Amazon A+ Content
* Shopify Development
* Automation Tools
* AI-Powered Business Solutions


---

## Disclaimer

This tool is intended for research, lead generation, and business development purposes. Users are responsible for ensuring compliance with Amazon's Terms of Service and applicable local regulations.

---

## License

Copyright © Muhammad Haseeb.

All Rights Reserved.
