Telegram Channel Scraper
========================

A tool for sraping public telegram channels, downloads all messages, media files, and channel metadata for offline viewing and analysis

Features
--------

 scraping complete public channel content
 Download all messages with timestamps and view counts
 Save images and video thumbnails locally
 Extract channel metadata (subscribers, media counts)
 Detect creation date
 Estimate channel origin based on message language
 Generate HTML reports for offline viewing
 Support for single channel or batch processing
 Proxy support for rate limit avoidance

Installation
------------

git clone https://github.com/Onchallange/telegram-scraper-osint
cd telegram-scraper-osint
pip install -r requirements.txt

Usage
-----

Scraping a single channel:

python3 main.py -c name -m 100

scraping multiple channels from file

create a file named groups.txt with one channel per line

exemple
telegram
etcetc name

Then run

python3 main.py -t groups.txt -m 200

Command line options:

-c, --channel    single channel username (without @)
-t, --targets    file containing list of channels
-m, --max        maximum messages to scrape
-d, --delay      delay between requests in seconds
-p, --proxy      proxy file for requests
-o, --output     custom output folder name

Using proxies:

Create a proxies.txt file with one proxy per line

0.1.2.3:8080
1.2.3.4:3128:username:pwd

Then run with proxy support

python3 main.py -c name -p proxies.txt

Requirements
------------

- Python 3.7 or higher
- curl_cffi for browser fingerprint simulation
- BeautifulSoup4 for HTML parsing
- langdetect for language analysis

Rate Limiting
-------------

Telegram may temporarily block IP addresses that send too many requests. 
The tool includes

 configurable delays between requests
 automatic retry on rate limit responses
 proxy rotation support for large archives

For scraping large channels (1000+ messages), it is recommended next

1. use delays of 2 3 seconds between requests
2. Use rotating proxies for multiple channels

Disclaimer
----------

This tool is for educational purposes and personal scraping of content you have permission to access
 Respect telegram's terms of service and the intellectual property rights of channel owners
 Do not use this tool for harassment, spam, or any malicious purpose

The author is not responsible for how this script is used 
By using this tool, you agree that you will comply with all applicable laws and regulations

License
-------

MIT License
