import os
from pathlib import Path
from random import randint
from urllib.parse import urlsplit
from os.path import join

import requests
from dotenv import load_dotenv


def get_response(url, params=None, headers=None, files=None, data=None):
    response = requests.get(url, params=params, data=data, files=files, headers=headers)
    response.raise_for_status()

    return response.json()


def get_media_path(name_path):
    media_path = Path(name_path)
    media_path.mkdir(parents=True, exist_ok=True)

    return media_path


def download_media(url, filename):
    response = requests.get(url)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)


def vk_request(http_method, method, **kwargs):
    url = f'https://api.vk.com/method/{method}'
    response = getattr(requests, http_method)(url, **kwargs)
    response.raise_for_status()

    return response.json()


def download_xkcd_comics(name_folder):
    url = 'https://xkcd.com/info.0.json'
    last_comics_num = get_response(url=url)['num']

    random_comics_num = randint(1, last_comics_num)

    url = f'https://xkcd.com/{random_comics_num}/info.0.json'
    response = get_response(url)

    folder = get_media_path(name_folder)

    url_split = urlsplit(response['img'])
    filepath = join(folder / url_split.path[8:])

    download_media(response['img'], filepath)

    return filepath, response['alt']


def get_groups(access_token):
    params = {
        'access_token': access_token,
        'v': 5.131,
    }

    return vk_request('get', 'groups.get', params=params)


def get_upload_url(access_token, app_id):
    params = {
        'access_token': access_token,
        'group_id': app_id,
        'v': 5.131,
    }

    return vk_request('get', 'photos.getWallUploadServer', params=params)


def upload_file(access_token, app_id, filename, caption):
    upload_server = get_upload_url(access_token, app_id)['response']

    with open(filename, 'rb') as file:
        files = {'photo': file}
        response = requests.post(upload_server['upload_url'], files=files)
        response.raise_for_status()

    data = {
        'access_token': access_token,
        'group_id': app_id,
        'user_id': upload_server['user_id'],
        'photo': response.json()['photo'],
        'server': response.json()['server'],
        'hash': response.json()['hash'],
        'caption': caption,
        'v': 5.131,
    }

    return vk_request('post', 'photos.saveWallPhoto', data=data)


def wall_post(access_token, owner_id, from_group, attachments, message):
    params = {
        'access_token': access_token,
        'owner_id': owner_id,
        'from_group': from_group,
        'attachments': attachments,
        'message': message,
        'v': 5.131,
    }

    return vk_request('get', 'wall.post', params=params)


def main():
    load_dotenv()
    app_id = os.environ['VK_APP_ID']
    access_token = os.environ['VK_ACCESS_TOKEN']
    name_folder = os.getenv('MEDIA_PATH', default='images')
    group_id = os.environ['VK_GROUP_ID']

    filepath, alt_message = download_xkcd_comics(name_folder)
    response = upload_file(access_token, app_id, filepath, alt_message)['response'][0]
    wall_post(access_token, -int(group_id), 1, f"photo{response['owner_id']}_{response['id']}", alt_message)
    os.remove(filepath)


if __name__ == '__main__':
    main()
