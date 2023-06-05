import os
from pathlib import Path
from random import randint
from urllib.parse import urlsplit
from os.path import join

import requests
from dotenv import load_dotenv


class ResponseError(BaseException):
    pass


def raise_vk_error_status(response):
    response.raise_for_status()
    try:
        raise ResponseError(response.json()['error']['error_msg'])
    except KeyError:
        pass


def get_media_path(name_path):
    media_path = Path(name_path)
    media_path.mkdir(parents=True, exist_ok=True)
    return media_path


def download_media(url, filename):
    response = requests.get(url)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)


def download_xkcd_comics(folder_name):
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    last_comics_num = response.json()['num']

    random_comics_num = randint(1, last_comics_num)

    url = f'https://xkcd.com/{random_comics_num}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    comics_response = response.json()

    folder = get_media_path(folder_name)

    url_split = urlsplit(comics_response['img'])
    filepath = join(folder / url_split.path[8:])

    download_media(comics_response['img'], filepath)

    return filepath, comics_response['alt']


def get_upload_url(access_token, app_id):
    params = {
        'access_token': access_token,
        'group_id': app_id,
        'v': 5.131,
    }
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    response = requests.get(url, params=params)
    raise_vk_error_status(response)
    return response.json()


def upload_file(access_token, app_id, filename, caption):
    upload_server = get_upload_url(access_token, app_id)['response']

    with open(filename, 'rb') as file:
        files = {'photo': file}
        response = requests.post(upload_server['upload_url'], files=files)

    raise_vk_error_status(response)
    file_response = response.json()

    params = {
        'access_token': access_token,
        'group_id': app_id,
        'user_id': upload_server['user_id'],
        'photo': file_response['photo'],
        'server': file_response['server'],
        'hash': file_response['hash'],
        'caption': caption,
        'v': 5.131,
    }
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    response = requests.post(url, params=params)
    raise_vk_error_status(response)
    return response.json()


def post_on_wall(access_token, owner_id, from_group, attachments, message):
    params = {
        'access_token': access_token,
        'owner_id': owner_id,
        'from_group': from_group,
        'attachments': attachments,
        'message': message,
        'v': 5.131,
    }
    url = 'https://api.vk.com/method/wall.post'
    response = requests.get(url, params=params)
    raise_vk_error_status(response)
    return response.json()


def main():
    load_dotenv()
    app_id = os.environ['VK_APP_ID']
    access_token = os.environ['VK_ACCESS_TOKEN']
    folder_name = os.getenv('MEDIA_PATH', default='images')
    group_id = os.environ['VK_GROUP_ID']

    filepath, alt_message = download_xkcd_comics(folder_name)
    try:
        response = upload_file(access_token, app_id, filepath, alt_message)['response'][0]
        post_on_wall(access_token, -int(group_id), 1, f"photo{response['owner_id']}_{response['id']}", alt_message)
    finally:
        os.remove(filepath)


if __name__ == '__main__':
    main()
