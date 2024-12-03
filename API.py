

import requests
import configparser
from pprint import pprint
import json
from tqdm import tqdm


config = configparser.ConfigParser()
config.read("settings.ini")
vk_token = config['Tokens']['access_token']
ya_token = config['Tokens']['ya_token']


class VK:

    def __init__(self, access_token, version='5.199'):
        self.base_address = 'https://api.vk.com/method/'
        self.params = {
            'access_token': access_token,
            'v': version
        }

    def users_info(self, user_id):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': user_id}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def get_user_friends(self, id_user, count = 5):
        url = f'{self.base_address}friends.get'
        params = {'user_id': id_user, 'fields': 'nickname', 'count': count}
        params.update(self.params)
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def get_user_photos(self, id_user, count=5, albom_id = 'profile'):
        url = f'{self.base_address}photos.get'
        params = {'owner_id': id_user, 'album_id': albom_id,'extended': '1', 'count': count}
        response = requests.get(url, params={**self.params, **params})
        return response.json()


class YA:
    def __init__(self, ya_token, access_token):
        self.yadi_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.headers = {
            'Authorization': ya_token
        }
        self.vk = VK(access_token)

    def ya_folder(self, limit = 20):
        params = {
            'path': f'disk:/',
            'limit': limit
        }
        response = requests.get(self.yadi_url, headers=self.headers, params=params)
        if response.status_code == 200:
            list_of_folders = []
            for i in response.json().get('_embedded', {}).get('items', []):
                if i.get ('type') == 'dir':
                    list_of_folders.append(i.get('name'))
            return list_of_folders

        else:
            print(f'Ошибка при получении списка папок: {response.status_code}')

    def ya_list_of_photos(self, folder_name = 'VK'):
        params = {
            'path': f'disk:/{folder_name}',

        }
        response = requests.get(self.yadi_url, headers=self.headers, params=params)
        if response.status_code == 200:
            list_of_files = []
            for i in response.json().get('_embedded', {}).get('items', []):
                if i.get ('type') :
                    list_of_files.append(i.get('name'))
            return list_of_files

        else:
            print(f'Ошибка при получении списка папок: {response.status_code}')

    def ya_create_folder(self, folder_name):
        params = {
            'path': folder_name
        }
        response = requests.put(self.yadi_url, headers=self.headers, params=params)
        if response.status_code == 201:
            print(f"Папка '{folder_name}' успешно создана")
        else:
            print(f"Ошибка создания папки '{folder_name}': {response.json()['message']}")

    def write_json (self, name, size):
        data = {'file_name': name,
                'size': size
                }
        with open('data.json', 'a') as file:
            json.dump(data, file)


    def upload_photos(self, id_user, folder_name = 'VK'):
        yadi_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        files = self.vk.get_user_photos(id_user=id_user).get('response', {}).get ('items')
        list_of_photos = self.ya_list_of_photos()
        with  tqdm(total= len(files), unit = 'file', desc = 'Uploading files') as pbar:
            for i in files:
                url = ''
                size = ''
                type_w_size = next((size for size in i['sizes'] if size['type'] == 'w'), None)
                if type_w_size:
                    url = type_w_size['url']
                    size = type_w_size.get('type')
                else:
                    url = i['sizes'][-1]['url']
                    size = i['sizes'][-1]['type']
                name_likes = f'{i.get('likes').get('count')}.jpg'
                name_date = f'{i.get('likes').get('count')}-{i.get('date')}.jpg'
                try:
                    if name_likes not in list_of_photos:
                        name = name_likes
                        params = {
                                'path': f'disk:/{folder_name}/{name}',
                                'url': url
                            }
                        response = requests.post(yadi_url, headers=self.headers, params=params)
                        list_of_photos.append(name)
                        if response.status_code == 202:
                            self.write_json(name, size)

                    elif name_date not in list_of_photos:
                        name = name_date
                        params = {
                            'path': f'disk:/{folder_name}/{name}',
                            'url': url
                        }
                        response = requests.post(yadi_url, headers=self.headers, params=params)
                        list_of_photos.append(name)
                        if response.status_code == 202:
                            self.write_json(name, size)

                    else:
                        print(f'Фото {url} уже загружено!')

                    pbar.update(1)
                except Exception as e:
                        # Вывод сообщения об ошибке в случае неудачной загрузки
                        print(f'Не удалось загрузить {url}: {e}')
        return



vk = VK(vk_token)


# pprint(vk.get_user_photos('891373795'))
# pprint(vk.get_user_friends('12405493'))

ya = YA(ya_token, vk_token)
# ya.ya_folder()
# ya.ya_create_folder('VK')
ya.upload_photos('891373795')

