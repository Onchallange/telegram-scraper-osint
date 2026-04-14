import os
import json
import re
from datetime import datetime
from langdetect import detect, DetectorFactory
from collections import Counter
from bs4 import BeautifulSoup
from curl_cffi import requests

DetectorFactory.seed = 0

def detect_country_from_messages(messages):
    if not messages:
        return 'Unknown'
    
    texts = []
    for msg in messages:
        if msg.get('text'):
            texts.append(msg['text'])
    
    lang_counts = Counter()
    for text in texts[:50]:
        try:
            if len(text) > 20:
                lang = detect(text)
                lang_counts[lang] += 1
        except:
            pass
    
    if not lang_counts:
        return 'Unknown'
    
    main_lang = lang_counts.most_common(1)[0][0]
    
    lang_country_map = {
        'ro': 'Romania',
        'ru': 'Russia',
        'uk': 'Ukraine',
        'en': 'English speaking',
        'es': 'Spain/Latin America',
        'fr': 'France',
        'de': 'Germany',
        'it': 'Italy',
        'pt': 'Portugal/Brazil',
        'tr': 'Turkey',
        'ar': 'Arab region',
        'hi': 'India',
        'zh-cn': 'China',
        'ja': 'Japan',
        'ko': 'Korea',
    }
    
    if main_lang in lang_country_map:
        return lang_country_map[main_lang]
    else:
        return main_lang

def get_channel_creation_date(channel_name, proxy=None):
    url = f"https://t.me/s/{channel_name}/1"
    
    try:
        if proxy:
            response = requests.get(url, timeout=30, proxies=proxy, impersonate="chrome")
        else:
            response = requests.get(url, timeout=30, impersonate="chrome")
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        service_date = soup.find('div', class_='tgme_widget_message_service_date')
        if service_date:
            date_text = service_date.get_text(strip=True)
            if date_text:
                return date_text
        
        time_elem = soup.find('time', class_='tgme_widget_message_date')
        if time_elem and time_elem.get('datetime'):
            dt = time_elem.get('datetime')
            try:
                d = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return d.strftime('%B %d, %Y')
            except:
                return dt
        
        return None
    except:
        return None

def get_channel_info(channel_name, proxy=None):
    url = f"https://t.me/s/{channel_name}"
    
    try:
        if proxy:
            response = requests.get(url, timeout=30, proxies=proxy, impersonate="chrome")
        else:
            response = requests.get(url, timeout=30, impersonate="chrome")
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        info = {
            'title': None,
            'description': None,
            'subscribers': None,
            'photos': None,
            'videos': None,
            'links': None,
            'username': channel_name
        }
        
        title_div = soup.find('div', class_='tgme_channel_info_header_title')
        if title_div:
            span = title_div.find('span')
            if span:
                info['title'] = span.get_text(strip=True)
        
        desc_div = soup.find('div', class_='tgme_channel_info_description')
        if desc_div:
            info['description'] = desc_div.get_text(strip=True)
        
        counters_div = soup.find('div', class_='tgme_channel_info_counters')
        if counters_div:
            counters = counters_div.find_all('div', class_='tgme_channel_info_counter')
            for counter in counters:
                value_span = counter.find('span', class_='counter_value')
                type_span = counter.find('span', class_='counter_type')
                if value_span and type_span:
                    value = value_span.get_text(strip=True)
                    ctype = type_span.get_text(strip=True).lower()
                    if 'subscriber' in ctype:
                        info['subscribers'] = value.replace(',', '')
                    elif 'photo' in ctype:
                        info['photos'] = value.replace(',', '')
                    elif 'video' in ctype:
                        info['videos'] = value.replace(',', '')
                    elif 'link' in ctype:
                        info['links'] = value.replace(',', '')
        
        if not info['title']:
            title_div = soup.find('div', class_='tgme_page_title')
            if title_div:
                span = title_div.find('span')
                if span:
                    info['title'] = span.get_text(strip=True)
        
        return info
    except:
        return None

def generate_html_report(channel_name, info, messages, output_folder):
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{info.get('title', channel_name)} - Telegram Scraper</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #0f0f0f; color: #e0e0e0; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{ background: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .message {{ background: #1e1e1e; padding: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 3px solid #2b9c5c; }}
        .message-text {{ margin: 10px 0; line-height: 1.5; }}
        .message-meta {{ font-size: 12px; color: #888; margin-top: 10px; }}
        .media {{ margin-top: 10px; }}
        .media img {{ max-width: 300px; max-height: 300px; margin-right: 10px; border-radius: 5px; }}
        .date {{ color: #2b9c5c; }}
        .views {{ color: #888; }}
        hr {{ border-color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{info.get('title', channel_name)}</h1>
            <p>@{channel_name}</p>
            <p>Subscribers: {info.get('subscribers', 'N/A')}</p>
            <p>Created: {info.get('creation_date', 'N/A')}</p>
            <p>Total messages scraped: {len(messages)}</p>
        </div>
'''
    
    for msg in messages:
        html_content += f'''
        <div class="message">
            <div class="message-meta">
                <span class="date">{msg.get('datetime', 'Unknown date')}</span>
                <span class="views"> | Views: {msg.get('views', '0')}</span>
            </div>
            <div class="message-text">{msg.get('text', 'No text')}</div>
'''
        if msg.get('media'):
            html_content += '<div class="media">'
            for media in msg['media']:
                if media['type'] == 'image' and media.get('saved_as'):
                    html_content += f'<img src="media/images/{media["saved_as"]}">'
            html_content += '</div>'
        
        html_content += '</div>\n'
    
    html_content += '''
    </div>
</body>
</html>
'''
    
    html_file = os.path.join(output_folder, f'{channel_name}_report.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return html_file
