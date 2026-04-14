import random

def load_proxies(proxy_file):
    proxies = []
    try:
        with open(proxy_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                proxies.append(line)
    except:
        pass
    return proxies

def parse_proxy(proxy_str):
    if not proxy_str:
        return None
    
    if '@' in proxy_str:
        user_pass, host_port = proxy_str.split('@')
        if ':' in user_pass:
            user, password = user_pass.split(':')
        else:
            user, password = user_pass, ''
        return {
            'http': f'http://{user}:{password}@{host_port}',
            'https': f'http://{user}:{password}@{host_port}'
        }
    else:
        return {
            'http': f'http://{proxy_str}',
            'https': f'http://{proxy_str}'
        }

def get_random_proxy(proxy_list):
    if not proxy_list:
        return None
    return parse_proxy(random.choice(proxy_list))
