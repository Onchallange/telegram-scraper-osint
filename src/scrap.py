import time
import re
import os
import hashlib
from bs4 import BeautifulSoup
from curl_cffi import requests

def get_channel_page(channel_name, before_id=None, proxy=None):
    base_url = f"https://t.me/s/{channel_name}"
    if before_id:
        url = f"{base_url}?before={before_id}"
    else:
        url = base_url
    
    try:
        if proxy:
            response = requests.get(url, timeout=30, proxies=proxy, impersonate="chrome")
        else:
            response = requests.get(url, timeout=30, impersonate="chrome")
        
        if response.status_code == 200:
            return response.text
        elif response.status_code == 429:
            return 'rate_limit'
        else:
            return None
    except:
        return None

def download_media(url, folder, proxy=None):
    try:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        ext = url.split('.')[-1].split('?')[0]
        if len(ext) > 5:
            ext = 'jpg'
        filename = f"{url_hash}.{ext}"
        filepath = os.path.join(folder, filename)
        
        if os.path.exists(filepath):
            return filename
        
        if proxy:
            response = requests.get(url, timeout=30, proxies=proxy, impersonate="chrome")
        else:
            response = requests.get(url, timeout=30, impersonate="chrome")
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filename
        return None
    except:
        return None

def parse_messages(html, channel_name, images_folder, videos_folder, proxy=None):
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    messages = []
    
    message_divs = soup.find_all('div', class_='tgme_widget_message')
    
    for div in message_divs:
        try:
            data_post = div.get('data-post', '')
            message_id = None
            if data_post:
                parts = data_post.split('/')
                if len(parts) > 1:
                    message_id = parts[-1]
            
            if not message_id:
                continue
            
            text_div = div.find('div', class_='tgme_widget_message_text')
            text = text_div.get_text(strip=True) if text_div else ''
            
            time_elem = div.find('time', class_='tgme_widget_message_date')
            datetime_str = None
            if time_elem:
                datetime_str = time_elem.get('datetime')
            
            views_elem = div.find('span', class_='tgme_widget_message_views')
            views = views_elem.get_text(strip=True) if views_elem else '0'
            
            author_elem = div.find('div', class_='tgme_widget_message_author')
            author = None
            if author_elem:
                author_name = author_elem.find('span')
                if author_name:
                    author = author_name.get_text(strip=True)
            
            media_list = []
            
            photo_wraps = div.find_all('a', class_='tgme_widget_message_photo_wrap')
            for wrap in photo_wraps:
                style = wrap.get('style', '')
                match = re.search(r"url\('([^']+)'\)", style)
                if match:
                    img_url = match.group(1)
                    saved = download_media(img_url, images_folder, proxy)
                    if saved:
                        media_list.append({
                            'type': 'image',
                            'url': img_url,
                            'saved_as': saved
                        })
                    else:
                        media_list.append({
                            'type': 'image',
                            'url': img_url,
                            'saved_as': None
                        })
            
            video_wraps = div.find_all('a', class_='tgme_widget_message_video_wrap')
            for wrap in video_wraps:
                style = wrap.get('style', '')
                match = re.search(r"url\('([^']+)'\)", style)
                if match:
                    video_url = match.group(1)
                    saved = download_media(video_url, videos_folder, proxy)
                    if saved:
                        media_list.append({
                            'type': 'video',
                            'url': video_url,
                            'saved_as': saved
                        })
                    else:
                        media_list.append({
                            'type': 'video',
                            'url': video_url,
                            'saved_as': None
                        })
            
            messages.append({
                'id': message_id,
                'url': f"https://t.me/{channel_name}/{message_id}",
                'text': text,
                'datetime': datetime_str,
                'views': views,
                'author': author,
                'media': media_list
            })
        except:
            continue
    
    return messages

def scrape_channel(channel_name, images_folder, videos_folder, max_messages=100, delay=1, proxy=None, callback=None):
    messages = []
    last_id = None
    empty_count = 0
    
    while len(messages) < max_messages and empty_count < 5:
        html = get_channel_page(channel_name, last_id, proxy)
        
        if html == 'rate_limit':
            if callback:
                callback('rate_limit', None)
            time.sleep(15)
            continue
        
        if not html:
            empty_count += 1
            time.sleep(delay)
            continue
        
        new_messages = parse_messages(html, channel_name, images_folder, videos_folder, proxy)
        
        if not new_messages:
            empty_count += 1
            time.sleep(delay)
            continue
        
        unique_new = []
        existing_ids = [m['id'] for m in messages]
        for msg in new_messages:
            if msg['id'] not in existing_ids:
                unique_new.append(msg)
        
        if not unique_new:
            empty_count += 1
            time.sleep(delay)
            continue
        
        for msg in unique_new:
            if len(messages) >= max_messages:
                break
            messages.append(msg)
            last_id = msg['id']
        
        empty_count = 0
        
        if callback:
            callback('progress', len(messages))
        
        time.sleep(delay)
    
    return messages
