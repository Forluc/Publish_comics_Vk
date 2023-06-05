import os

import requests
from dotenv import load_dotenv


def main():
    load_dotenv()
    client_id = os.environ['VK_APP_ID']
    params = {
        'client_id': client_id,
        'scope': 'photos, groups, wall',
    }
    url = 'https://oauth.vk.com/authorize'
    response = requests.get(url, params=params)
    response.raise_for_status()
    print(response.url)


if __name__ == '__main__':
    main()
