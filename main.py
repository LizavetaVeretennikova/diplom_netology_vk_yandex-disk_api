from urllib.parse import urlencode
import requests
from pprint import pprint
import time
from time import sleep
import json
import yadisk
from tqdm.auto import tqdm

# app_id = '51775754'
# oauth_base_url = 'https://oauth.vk.com/authorize'
# params = {
#     'client_id': app_id,
#     'redirect_uri': 'https://oauth.vk.com/blank.html',
#     'display': 'page',
#     'scope': 'photos',
#     'response_type': 'token',
# }
# oauth_url = f'{oauth_base_url}?{urlencode(params)}'
# print(oauth_url)
from configuration import token
class VK_API_client:
    #Настройка параметров при работу с api vk
    api_base_url = 'https://api.vk.com/method'
    def __init__(self, token, expires_in, user_id):
        self.access_token = token
        self.expires_in = expires_in
        self.user_id = user_id

    def get_commons_params(self):
        return {'access_token': self.access_token, 'v': '5.154'}

    def _build_url(self, api_method):
        return f'{self.api_base_url}/{api_method}'

    def get_vk_client_info(self):
        user_url = f'{self.api_base_url}/users.get'
        user_id = input("Добро пожаловать! Введите свой id или screen_name: ")
        if user_id == "":
            user_id = self.user_id
        params = self.get_commons_params()
        params.update({'user_ids': user_id, 'fields': 'screen_name'})
        response = requests.get(user_url, params=params).json()
        print(response)
        if 'error' in response.keys():
            error = response['error']
            print(f'Ошибка: {error}')
            self.user_id = None
            return self.user_id
        else:
            self.user_id = response['response'][0]['id']
            if 'screen_name' in response['response'][0].keys():
                self.screen_name = response['response'][0]['screen_name']
            else:
                print(f'screen_name "{user_id}" не существует.')
                return self.user_id

    def get_profile_photos(self):
#Получение параметров фотографий профиля
        params = self.get_commons_params()
        params.update({'owner_id': self.user_id,'album_id': 'profile', 'extended': '1', 'photo_sizes': '1', 'count': 5})
        response = requests.get(self._build_url('photos.get'), params=params).json()
#Количество сохраненных фотографий
        items_response = response['response']['items']
#Формирование списка для json-файла
        json_file = []
#Формирование списка url для ЯД
        yandex_disk_file = []
#Формирование списка имен для фотографий
        name_photos = []
#Количество лайков
        for item_response in items_response:
            like = item_response['likes']['count']
#Установка даты загрузки фотографий профиля
            date_upload_photo = time.strftime('%y-%m-%d', time.gmtime(item_response['date']))
#Формирование названий фотографий для ЯД
            if like in name_photos:
                file_name = f"{like}-{date_upload_photo}.jpg"
            else:
                file_name = f"{like}.jpg"
            if like not in name_photos:
                name_photos.append(like)
#Формирование ссылки для ЯД
            photo_url, size = self.max_sizes_profile_photo(item_response['sizes'])
#Формирование словарей для json_файла
            js_file = {
                "file_name": file_name,
                       "size": size,
                       }
#Формирование словаря для ЯД
            ya_d_file = {
                "file_name": file_name,
                "size": size,
                "url": photo_url,
            }
            json_file.append(js_file)
            yandex_disk_file.append(ya_d_file)
#Формирование json-файлов
        with open('json_file.json', 'w') as f:
            json.dump(json_file, f, ensure_ascii=False, indent=2)

        with open('yandex_disk_file.json', 'w') as file:
            json.dump(yandex_disk_file, file, ensure_ascii=False, indent=2)
        return json_file, yandex_disk_file
    def max_sizes_profile_photo(self, sizes):
        #Фото от максимального до минимального размера
        types = ['w', 'z', 'y', 'r', 'q', 'p', 'o', 'x', 'm', 's']
        #Выбор максимального размера
        for type in types:
            for size in sizes:
                if size['type'] == type:
                    return size['url'], type



class YADISK_API_client:
    def yandex_api(self):
        token = input('Введите токен с Полигона Яндекс.Диска: ')
        headers = {
            "Accept": "application/json",
            'Authorization': "OAuth " + token
        }
        # Создание папки на Яндекс.Диске
        name_folder = input('Введите название папки: ')
        params = {'path': name_folder}
        response = requests.put('https://cloud-api.yandex.net/v1/disk/resources',
                                params=params, headers=headers)
        print(response.json())

        # Запрос адреса загрузки
        with open('yandex_disk_file.json', 'r') as f:
            photo_yad = json.load(f)
        fields = 'file_name'
        for photo in photo_yad:
            file_name = photo['file_name']
            path = f"{name_folder}/{file_name}"
            url = photo["url"]
            params = {
                'path': path,
                'url': url,
                'fields': fields
            }
            response = requests.post("https://cloud-api.yandex.net/v1/disk/resources/upload", params=params,
                                     headers=headers)
            print(response.json())
        #Прогресс-бар
        x = 0
        for photo in tqdm(photo_yad):
            time.sleep(1)
            x +=1


if __name__ == '__main__':
    vk_client = VK_API_client(token, 31536000, "")
    vk_client.get_vk_client_info()
    vk_client.get_profile_photos()
    yadisk_client = YADISK_API_client()
    yadisk_client.yandex_api()
