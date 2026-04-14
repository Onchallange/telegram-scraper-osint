#!/usr/bin/env python3
import os
import sys
import json
import time
import argparse
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from proxy import load_proxies, get_random_proxy
from scrap import scrape_channel
from utils import (
    get_channel_info,
    get_channel_creation_date,
    detect_country_from_messages,
    generate_html_report
)

def gradient_text(text, start_color, end_color):
    result = ''
    for i, char in enumerate(text):
        if len(text) > 1:
            ratio = i / len(text)
        else:
            ratio = 0
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        result += f'\033[38;2;{r};{g};{b}m{char}'
    return result + Style.RESET_ALL

def print_banner():
    banner = '''
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                 TELEGRAM SCRAPER                         ┃
┃               Multi-channel + OSINT                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
'''
    for line in banner.split('\n'):
        if line.strip():
            print(gradient_text(line, (0, 255, 135), (0, 185, 255)))

def create_output_folder(channel_name=None):
    if channel_name:
        folder_name = f'scraped_{channel_name}'
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        folder_name = f'output_{timestamp}'
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

def load_targets(target_file):
    targets = []
    try:
        with open(target_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    line = line.replace('@', '').replace('https://t.me/', '').replace('/s/', '')
                    targets.append(line)
    except:
        pass
    return targets

def progress_callback(event, value):
    if event == 'progress':
        sys.stdout.write(f'\r{Fore.CYAN}[+] Scraped: {value} messages')
        sys.stdout.flush()
    elif event == 'rate_limit':
        print(f'\n{Fore.YELLOW}[!] Rate limit hit, waiting...')

def process_channel(channel, proxy, max_messages, delay, output_base=None):
    print(f'\n{Fore.CYAN}[+] Processing: @{channel}')
    
    if output_base:
        output_folder = os.path.join(output_base, channel)
    else:
        output_folder = create_output_folder(channel)
    
    os.makedirs(output_folder, exist_ok=True)
    
    images_folder = os.path.join(output_folder, 'media', 'images')
    videos_folder = os.path.join(output_folder, 'media', 'videos')
    os.makedirs(images_folder, exist_ok=True)
    os.makedirs(videos_folder, exist_ok=True)
    
    channel_info = get_channel_info(channel, proxy)
    
    if not channel_info:
        print(f'{Fore.RED}[!] Failed to fetch channel info')
        return None
    
    if channel_info.get('title'):
        print(f'{Fore.GREEN}[+] Title: {channel_info["title"]}')
    
    if channel_info.get('subscribers'):
        print(f'{Fore.GREEN}[+] Subscribers: {channel_info["subscribers"]}')
    
    creation_date = get_channel_creation_date(channel, proxy)
    if creation_date:
        print(f'{Fore.GREEN}[+] Created: {creation_date}')
        channel_info['creation_date'] = creation_date
    
    print(f'{Fore.CYAN}[+] Scraping messages... (this may take a while)')
    
    messages = scrape_channel(
        channel,
        images_folder,
        videos_folder,
        max_messages=max_messages,
        delay=delay,
        proxy=proxy,
        callback=progress_callback
    )
    
    print()
    
    if not messages:
        print(f'{Fore.YELLOW}[!] No messages found')
        return None
    
    country = detect_country_from_messages(messages)
    print(f'{Fore.GREEN}[+] Estimated country: {country}')
    
    media_count = 0
    for msg in messages:
        media_count += len(msg.get('media', []))
    
    print(f'{Fore.GREEN}[+] Media files saved: {media_count}')
    
    channel_data = {
        'channel': channel,
        'info': channel_info,
        'estimated_country': country,
        'scraped_at': datetime.now().isoformat(),
        'total_messages': len(messages),
        'total_media': media_count,
        'messages': messages
    }
    
    data_file = os.path.join(output_folder, 'data.json')
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(channel_data, f, indent=2, ensure_ascii=False)
    
    info_file = os.path.join(output_folder, 'info.txt')
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"Channel: @{channel}\n")
        f.write(f"Name: {channel_info.get('title', 'N/A')}\n")
        if channel_info.get('description'):
            f.write(f"Description: {channel_info['description']}\n")
        if channel_info.get('subscribers'):
            f.write(f"Subscribers: {channel_info['subscribers']}\n")
        if channel_info.get('creation_date'):
            f.write(f"Created: {channel_info['creation_date']}\n")
        f.write(f"Estimated country: {country}\n")
        f.write(f"Messages scraped: {len(messages)}\n")
        f.write(f"Media files: {media_count}\n")
    
    html_file = generate_html_report(channel, channel_info, messages, output_folder)
    print(f'{Fore.GREEN}[+] HTML report: {html_file}')
    
    return {
        'title': channel_info.get('title'),
        'subscribers': channel_info.get('subscribers'),
        'country': country,
        'messages': len(messages),
        'media': media_count,
        'created': channel_info.get('creation_date'),
        'folder': output_folder
    }

def main():
    parser = argparse.ArgumentParser(description='Telegram Channel Scraper')
    parser.add_argument('-c', '--channel', type=str, help='Single channel name (without @)')
    parser.add_argument('-t', '--targets', type=str, help='File with channel names')
    parser.add_argument('-m', '--max', type=int, default=100, help='Max messages per channel')
    parser.add_argument('-d', '--delay', type=float, default=1.0, help='Delay between requests')
    parser.add_argument('-p', '--proxy', type=str, help='Proxy file (optional)')
    parser.add_argument('-o', '--output', type=str, help='Output folder name')
    
    args = parser.parse_args()
    
    print_banner()
    
    if not args.channel and not args.targets:
        print(f'{Fore.RED}[!] You must specify either -c (channel) or -t (targets file)')
        print(f'{Fore.YELLOW}[*] Examples:')
        print(f'{Fore.YELLOW}    python3 main.py -c durov -m 50')
        print(f'{Fore.YELLOW}    python3 main.py -t groups.txt -m 100')
        sys.exit(1)
    
    proxy_list = []
    if args.proxy and os.path.exists(args.proxy):
        proxy_list = load_proxies(args.proxy)
        if proxy_list:
            print(f'{Fore.GREEN}[+] Loaded {len(proxy_list)} proxies')
    
    all_results = {}
    
    if args.channel:
        channel = args.channel.replace('@', '').replace('https://t.me/', '').strip()
        proxy = get_random_proxy(proxy_list) if proxy_list else None
        
        result = process_channel(channel, proxy, args.max, args.delay, args.output)
        if result:
            all_results[channel] = result
    else:
        if not os.path.exists(args.targets):
            print(f'{Fore.RED}[!] Targets file not found: {args.targets}')
            sys.exit(1)
        
        targets = load_targets(args.targets)
        if not targets:
            print(f'{Fore.RED}[!] No targets found in {args.targets}')
            sys.exit(1)
        
        print(f'{Fore.GREEN}[+] Loaded {len(targets)} channels')
        
        for idx, channel in enumerate(targets, 1):
            print(f'\n{Fore.CYAN}[{idx}/{len(targets)}]')
            
            proxy = get_random_proxy(proxy_list) if proxy_list else None
            
            result = process_channel(channel, proxy, args.max, args.delay, args.output)
            if result:
                all_results[channel] = result
            
            if idx < len(targets):
                time.sleep(2)
    
    if all_results:
        if args.output:
            summary_file = os.path.join(args.output, 'summary.json')
        else:
            summary_file = 'summary.json'
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f'\n{Fore.CYAN}┌─────────────────────────────────────────────────────────────────┐')
        print(f'{Fore.CYAN}│{Fore.WHITE}                       SCRAPE COMPLETE                         {Fore.CYAN}│')
        print(f'{Fore.CYAN}├─────────────────────────────────────────────────────────────────┤')
        print(f'{Fore.CYAN}│{Fore.WHITE} Total channels: {Fore.GREEN}{len(all_results)}{" " * (47 - len(str(len(all_results))))}{Fore.CYAN}│')
        
        total_msgs = sum([r['messages'] for r in all_results.values()])
        total_media = sum([r['media'] for r in all_results.values()])
        
        print(f'{Fore.CYAN}│{Fore.WHITE} Total messages: {Fore.GREEN}{total_msgs}{" " * (47 - len(str(total_msgs)))}{Fore.CYAN}│')
        print(f'{Fore.CYAN}│{Fore.WHITE} Total media: {Fore.GREEN}{total_media}{" " * (48 - len(str(total_media)))}{Fore.CYAN}│')
        print(f'{Fore.CYAN}└─────────────────────────────────────────────────────────────────┘')
        
        print(f'\n{Fore.GREEN}[+] Done. Summary saved to {summary_file}')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f'\n{Fore.RED}[!] Interrupted')
        sys.exit(0)
    except Exception as e:
        print(f'\n{Fore.RED}[!] Error: {str(e)[:100]}')
        sys.exit(1)
