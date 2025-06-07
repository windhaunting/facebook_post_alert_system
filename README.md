# Facebook Marketplace & Group Alert System

Tired of constantly checking Facebook Marketplace or private groups for something you need—especially when it's free—only to miss it because you weren’t fast enough?  
I was in the same boat, wasting time manually monitoring posts.

So, I built this lightweight alert system on my MacBook.

---

## 🚀 What It Does

This system automatically scans **Facebook Marketplace** and **private groups** (that you're a member of) for posts matching your specified keywords.  
When a match is found, you'll receive a **desktop notification instantly**—so you never miss a great deal again.

---

## ✨ Key Features

- 🔍 Monitors both Marketplace and private group posts
- 🛎️ Sends real-time **MacBook notifications** for matched keywords
- 📝 Logs matched results into a `matched_posts.txt` file for easy reference

If you're searching for specific items but don’t have time to watch Facebook all day, this tool is for you.

---

## 🛠️ How to Use

### 1. Create a `.env` File

Include the following environment variables in a `.env` file:

```env
FB_EMAIL=             # Your Facebook email
FB_PASSWORD=          # Your Facebook password
KEYWORDS=             # Comma-separated keywords (e.g. toy,bike)
GROUP_URLS=           # Comma-separated list of Facebook group URLs
FETCH_INTERVAL_MINUTES=          # How often to fetch posts (in minutes)
GROUP_POST_LOOKBACK_HOURS=       # How far back to look in group posts (in hours)
MARKETPLACE_ZIP=      # Zip code for Marketplace search
MARKETPLACE_RADIUS=   # Search radius in miles
MARKETPLACE_LATITUDE= # Latitude of the Marketplace search center
MARKETPLACE_LONGITUDE=# Longitude of the Marketplace search center

# Create and activate a virtual environment
conda create -n fb_notify python=3.10
conda activate fb_notify

# Install dependencies
conda install pip
pip install -r requirements.txt

# Install Playwright browser drivers
playwright install

# Make sure your .env file is configured
# Then start the alert system
python monitor_notify.py
```

### 2. Set Up and Run the System  
```
# Create and activate a virtual environment
conda create -n fb_notify python=3.10
conda activate fb_notify

# Install dependencies
conda install pip
pip install -r requirements.txt

# Install Playwright browser drivers
playwright install

# Make sure your .env file is configured
# Then start the alert system
python monitor_notify.py
```
