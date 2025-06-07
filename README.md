Facebook Marketplace & Group Alert System
Tired of constantly checking Facebook Marketplace or private groups for something you need—especially when it's free—only to miss it because you weren’t fast enough? I was in the same boat, wasting time monitoring posts manually.

So, I built this lightweight alert system on my MacBook.

What It Does
This system automatically scans Facebook Marketplace and private groups you're a member of for posts that match your specified keywords. When a match is found, you'll receive a desktop notification instantly—so you never miss a good deal again.

Key Features
🔍 Monitors both Marketplace and private group posts

🛎️ Sends real-time MacBook notifications for matched keywords

📝 Logs results in a matched_posts.txt file for easy reference

If you're on the lookout for specific items but don’t have time to watch Facebook all day, this tool is for you.


How to use:

1. Create .env file to include this information:  
FB_EMAIL=                    # Your facebook email  
FB_PASSWORD=                 # Your facebook password  
KEYWORDS=                    # keywords for posts that your have interest. e.g. toy, bike.  
GROUP_URLS=                  # some public groups or private groups that you are a member of  
FETCH_INTERVAL_MINUTES=             # how often to fetch post to alert in minute  
GROUP_POST_LOOKBACK_HOURS=         # How many hours of group post to search back  
MARKETPLACE_ZIP=                  # the zip code of marketplace search  
MARKETPLACE_RADIUS=               # the range of the marketplace search  
MARKETPLACE_LATITUDE=             # the latitude of the marketplace search center  
MARKETPLACE_LONGITUDE=            # the latitude of the marketplace search center  

2. Run the system  

conda create -n fb_notify python=3.10  
conda activate fb_notify  
conda install pip  
pip install -r requirements.txt  
playwright install  
#Add and Edit your .env file for parameters  
python monitor_notify.py# facebook_post_alert_system  
