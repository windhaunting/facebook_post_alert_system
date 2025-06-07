import os
import time
import hashlib
import subprocess
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import re
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('punkt_tab')

# Load environment variables from .env file
load_dotenv()

FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")
KEYWORDS = [kw.strip().lower() for kw in os.getenv("KEYWORDS", "books,kids").split(",")]
GROUP_URLS = [url.strip() for url in os.getenv("GROUP_URLS", "https://www.facebook.com/groups/378646223981959").split(",")]
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "5"))
ZIP_CODE = os.getenv("MARKETPLACE_ZIP", "18045")
RADIUS_MILES = float(os.getenv("MARKETPLACE_RADIUS", "20"))
LATITUDE = float(os.getenv("MARKETPLACE_LATITUDE", "40.6912"))
LONGITUDE = float(os.getenv("MARKETPLACE_LONGITUDE", "-75.2207"))
GROUP_POST_LOOKBACK_HOURS = int(os.getenv("GROUP_POST_LOOKBACK_HOURS", "6"))
DATA_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "1"))
FETCH_SOURCES = os.getenv("FETCH_SOURCES", "both").lower()

MATCHED_POSTS_FILE = "matched_posts.txt"
SEEN_POSTS_FILE = "seen_posts.txt"
MARKETPLACE_URL = (
    f"https://www.facebook.com/marketplace/{ZIP_CODE}/"
    f"?deliveryMethod=local_pick_up"
    f"&exact=false"
    f"&latitude={LATITUDE}"
    f"&longitude={LONGITUDE}"
    f"&radius={RADIUS_MILES}"
    f"&minPrice=0"
    f"&maxPrice=50"
)
seen_posts = set()
geolocator = Nominatim(user_agent="fb_marketplace_monitor")
lemmatizer = WordNetLemmatizer()

# Validate critical environment variables
if not FB_EMAIL or not FB_PASSWORD:
    print("Environment variables FB_EMAIL and FB_PASSWORD must be set!")
    raise ValueError("Environment variables FB_EMAIL and FB_PASSWORD must be set!")

def load_seen_posts():
    global seen_posts
    seen_posts.clear()
    if os.path.exists(SEEN_POSTS_FILE):
        with open(SEEN_POSTS_FILE, 'r') as f:
            seen_posts.update(line.strip() for line in f if line.strip())
    print(f"Loaded {len(seen_posts)} seen posts from file.")

def save_seen_post(post_id):
    if post_id not in seen_posts:
        seen_posts.add(post_id)
        with open(SEEN_POSTS_FILE, 'a') as f:
            f.write(post_id + "\n")
        print(f"Saved post ID {post_id} to seen posts.")

def log_matched_post(username, content, group_url=None, post_time=None, found_time=None):
    try:
        cleaned_content = content.strip()
        now = found_time or datetime.now()
        cutoff = now - timedelta(days=DATA_RETENTION_DAYS)

        # Format post time
        post_time_str = post_time.strftime('%Y-%m-%d %H:%M:%S') if post_time else "Unknown"

        # Create entry for the matched post
        new_entry = [
            f"User: {username}",
            f"Content: {cleaned_content}",
            f"Group URL: {group_url}" if group_url else "",
            f"Post Time: {post_time_str}",
            f"Found: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            "----------------------------------------"
        ]

        # Read existing posts
        if os.path.exists(MATCHED_POSTS_FILE):
            with open(MATCHED_POSTS_FILE, 'r') as f:
                existing_posts = f.readlines()
        else:
            existing_posts = []

        # Prepend new post at the top
        updated_posts = "\n".join(new_entry) + "\n" + "".join(existing_posts)

        # Write back to file
        with open(MATCHED_POSTS_FILE, 'w') as f:
            f.write(updated_posts)

        print(f"Logged matched post by {username}.")
    except Exception as e:
        print(f"Failed to log matched post: {e}")


def get_distance_miles(location_name):
    try:
        location = geolocator.geocode(location_name)
        if location:
            lat_lon = (location.latitude, location.longitude)
            target = (float(LATITUDE), float(LONGITUDE))
            return geodesic(lat_lon, target).miles
    except Exception as e:
        print(f"[ERROR] Failed to geocode {location_name}: {e}")
    return float('inf')

def extract_location_from_text(text):
    if ";" in text:
        parts = text.split(";")
        return parts[1].strip()
    return None

def hash_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def show_notification(title, message):
    try:
        message = message.replace('"', '\"')
        script = f'display notification "{message}" with title "{title}" sound name "default"'
        subprocess.run(["osascript", "-e", script])
        print(f"Notification sent: {title} - {message}")
    except Exception as e:
        print(f"Failed to send notification: {e}")

def contains_keywords(text):
    words = word_tokenize(text.lower())
    lemmatized = [lemmatizer.lemmatize(word) for word in words]
    result = any(kw in lemmatized for kw in KEYWORDS)
    print(f"Keyword match {'found' if result else 'not found'} in text: {text[:200]}")
    return result

def wait_for_login(page):
    print("Waiting for Facebook login...")
    page.goto("https://www.facebook.com")
    try:
        page.wait_for_selector("[aria-label='Create a post']", timeout=60000)
        print("Login detected.")
    except Exception:
        print("Login not detected. Please check credentials or session.")
        raise RuntimeError("Login not detected.")

def scrape_groups(page):
    for group_url in GROUP_URLS:
        print(f"Navigating to group: {group_url}")
        try:
            page.goto(group_url)

            # Wait for the post container class to load
            page.wait_for_selector('div.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x1vvkbs.x126k92a', timeout=10000)
            print("Main post content loaded.")

            # Scroll to load more posts
            for _ in range(10):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                time.sleep(2)

            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # Find all post containers
            post_containers = soup.find_all('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs x126k92a')
            print(f"Found {len(post_containers)} posts in the group page.")

            for post_container in post_containers:
                # DEBUG: Print the raw HTML of the post container
                #print("DEBUG: Post Container HTML:")
                #print(post_container.prettify())

                # Extract post content
                post_body = post_container.get_text(" ", strip=True).strip()
                #print("post_body: ", post_body)

                # Filter out irrelevant content
                if not post_body or len(post_body) < 20:
                    continue  # Skip short or irrelevant content

                # Navigate to the parent or sibling container to find the username
                parent = post_container.find_parent()
                if parent:
                    username_tag = parent.find('span', class_='html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs')
                else:
                    username_tag = None

                # Extract username
                username = username_tag.get_text(strip=True) if username_tag else "Unknown"
                #print("Username: ", username)

                # Debugging: Check extracted values
                #print("Post Content: ", post_body)

        except Exception as e:
            print(f"Error while processing group {group_url}: {e}")

def parse_post_time(post_time_text):
    """
    Parse the post time text into a datetime object.
    Example: "5 minutes ago", "2 hours ago", "yesterday", or a specific datetime.
    """
    now = datetime.now()
    if "minute" in post_time_text:
        minutes = int(re.search(r'\d+', post_time_text).group())
        return now - timedelta(minutes=minutes)
    elif "hour" in post_time_text:
        hours = int(re.search(r'\d+', post_time_text).group())
        return now - timedelta(hours=hours)
    elif "yesterday" in post_time_text.lower():
        return now - timedelta(days=1)
    else:
        # Try to parse specific datetime formats, if available
        try:
            return datetime.strptime(post_time_text, "%b %d at %I:%M %p")  # Example: "May 24 at 5:30 PM"
        except ValueError:
            return None  # If parsing fails, return None


from bs4 import BeautifulSoup
import time
import re

def scrape_marketplace(page):
    try:
        print(f"Navigating to Marketplace: {MARKETPLACE_URL}")
        page.goto(MARKETPLACE_URL)
        page.wait_for_timeout(5000)

        # Scroll the page multiple times to load more listings
        for _ in range(5):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            time.sleep(2)

        # Parse the page content using BeautifulSoup
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        # Find all marketplace listings
        listings = soup.find_all('a', href=re.compile(r'/marketplace/item/'))
        print(f"Found {len(listings)} marketplace listings.")

        for listing in listings:
            raw_href = listing.get('href')
            if not raw_href:
                continue

            # Clean the URL (remove query params or tracking)
            clean_path = raw_href.split('?')[0].split('&')[0]
            post_url = "https://www.facebook.com" + clean_path

            # Generate a consistent and unique ID from the clean path
            post_id = hash_text(clean_path)
            if post_id in seen_posts:
                continue

            # Extract title and content
            title_elem = listing.find('span')
            title = title_elem.get_text(" ", strip=True) if title_elem else ""

            content_elem = listing.find('div')
            content = content_elem.get_text(" ", strip=True) if content_elem else "No description provided"

            if not title:
                continue

            if contains_keywords(title) or contains_keywords(content):
                log_matched_post("Marketplace", f"Title: {title}\nContent: {content}\nURL: {post_url}")
                save_seen_post(post_id)
                show_notification("Matched Marketplace Post", f"{title[:100]}")

    except Exception as e:
        print(f"Error while scraping marketplace: {e}")


def main():
    load_seen_posts()
    check_marketplace = FETCH_SOURCES in ["both", "marketplace"]
    check_groups = FETCH_SOURCES in ["both", "groups"]

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(user_data_dir="fb_user_data", headless=False)
        page = browser.new_page()
        wait_for_login(page)

        try:
            while True:
                if check_groups:
                    scrape_groups(page)
                if check_marketplace:
                    scrape_marketplace(page)
                print(f"Waiting {FETCH_INTERVAL_MINUTES} minutes before next check...")
                time.sleep(FETCH_INTERVAL_MINUTES * 60)
        except KeyboardInterrupt:
            print("Shutdown requested. Closing browser...")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
