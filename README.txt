# Amazon.de Scraper

A professional Amazon Germany lead generation and seller research tool built for Amazon service providers, agencies, and consultants.

Developed by **Muhammad Haseeb**
Founder, Advertpreneur

---

## Overview

Amazon.de Scraper is a Flask and Playwright powered application that automatically collects seller information from Amazon Germany search results.

The tool captures both organic and sponsored listings, extracts seller details, and exports qualified leads into CSV format for outreach, research, and business development.

---

## Features

* Automated Amazon.de scraping
* Real-time dashboard updates
* Supports 1–5 pages per search
* Captures Sponsored and Organic listings
* Automatically skips Amazon-owned listings
* CSV export functionality
* Pre-configured Berlin delivery ZIP code (10115)
* Service tagging for outreach campaigns
* Browser automation powered by Playwright

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

### 3. Install Playwright Browser

```bash
playwright install chromium
```

Installation is now complete.

---

## Running the Application

Start the application:

```bash
python app.py
```

Open your browser and visit:

```text
http://localhost:5000
```

---

## Usage

### Step 1

Enter an Amazon Germany keyword.

Examples:

* tote bags
* water bottle
* kitchen organizer
* yoga mat

### Step 2

Choose the number of search result pages to scrape.

Supported range:

* 1 page
* 2 pages
* 3 pages
* 4 pages
* 5 pages

### Step 3

Click **Start Scraping**.

A visible Chromium browser window will launch automatically and begin collecting data.

### Step 4

Monitor results in real time through the dashboard.

### Step 5

When scraping is complete, click **Download CSV** to export results.

---

## Service Categories

The scraper automatically prepares service values that can be used in outreach workflows:

* Amazon SEO
* Listing Images
* PPC Management
* A+ Content

---

## Important Notes

* Berlin ZIP Code **10115** is applied automatically.
* Amazon Retail listings are excluded.
* Sponsored listings are clearly tagged.
* Organic listings are clearly tagged.
* Exported CSV files are saved inside the `exports` directory.
* Keep the terminal window running while scraping.
* Do not manually close the browser window opened by Playwright.

---

## Project Structure

```text
amazon_de_scraper/
│
├── app.py
│   └── Main Flask application
│
├── scraper.py
│   └── Amazon scraping logic
│
├── requirements.txt
│   └── Python dependencies
│
├── templates/
│   └── index.html
│       └── Dashboard interface
│
├── exports/
│   └── Generated CSV files
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
* JavaScript

---

## Author

**Muhammad Haseeb**
Founder & Lead Developer — Advertpreneur

Specializing in:

* Amazon SEO
* Amazon PPC
* A+ Content
* Shopify Development
* Automation Tools
* AI-Powered Business Solutions

---

## License

This project is proprietary software.

Copyright © Muhammad Haseeb.

All rights reserved.
