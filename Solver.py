import json
import requests
import base64
import time
import random
from urllib.parse import urlencode
api_captcha = "https://tikapis.com/api/captcha"
class Solver:
    def __init__(self, device_info, _host):
        self.__host = _host
        self.__device = device_info
        self.__client = requests.Session()
    def __params(self):
        params = {
            "lang": "en",
            "app_name": self.__device["app_name"],
            "iid": self.__device["install_id"],
            "did": self.__device["device_id"],
            "device_id": self.__device["device_id"],
            "aid": self.__device["aid"],
            "os_type": "0",
            "tmp": f"{int(time.time())}{random.randint(111, 999)}",
            "platform": "app",
            "webdriver": "false",
            "verify_host": f"https://{self.__host}/",
            "locale": self.__device["lang_b"],
            "vc": self.__device["app_version"],
            "app_version": self.__device["app_version"],
            "resolution": self.__device["resolution"],
            "device_brand": self.__device["device_brand"],
            "device_model": self.__device["device_model"],
            "os_name": "Android",
            "challenge_code": "1105",
        }
        return urlencode(params)
    def __headers(self):
        headers = {
            "Fastly-Client-IP": '{}.{}.{}.{}'.format(*random.sample(range(0, 255), 4)),
        }
        return headers
    def __get_challenge(self):
        for _ in range(3):
            try:
                response = self.__client.get(
                    f"https://{self.__host}/captcha/get?{self.__params()}",
                    headers=self.__headers()
                )
                response.raise_for_status()
                data = response.json()
                if 'data' in data and 'question' in data['data'] and 'tip_y' in data['data']['question']:
                    return data
            except Exception as e:
                print(f"Error retrieving captcha challenge: {e}")
                time.sleep(1) 
        raise Exception(
            "Failed to retrieve captcha challenge after 3 attempts")
    def api_captcha_solver(self, puzzle, piece):
        puzzle_str = puzzle.decode('utf-8') if isinstance(puzzle, bytes) else puzzle
        piece_str = piece.decode('utf-8') if isinstance(piece, bytes) else piece
        body = {
            "puzzle": puzzle_str,
            "piece": piece_str,
        }
        response = self.__client.post(
            api_captcha,
            headers={
                'Content-Type': 'application/json',
                "api-key": API_KEY
            },
            data=json.dumps(body)
        )
        return response.json()
    def __solve_captcha(self, url_1, url_2):
        puzzle = base64.b64encode(self.__client.get(url_1).content)
        piece = base64.b64encode(self.__client.get(url_2).content)
        maxloc = self.api_captcha_solver(puzzle, piece)
        time.sleep(random.uniform(0.8, 1.3))
        return maxloc
    def __post_captcha(self, solve):
        body = {
            "modified_img_width": 552,
            "id": solve["id"],
            "mode": "slide",
            "reply": list(
                {
                    "relative_time": i * solve["randlenght"],
                    "x": round(
                        solve["maxloc"] / (solve["randlenght"] / (i + 1))
                    ),
                    "y": solve["tip"],
                }
                for i in range(
                    solve["randlenght"]
                )
            ),
        }
        headers = self.__headers()
        headers.update({"content-type": "application/json"})
        response = self.__client.post(
            f"https://{self.__host}/captcha/verify?{self.__params()}",
            headers=headers,
            json=body
        )
        return response.json()
    def solve_captcha(self):
        captcha_challenge = self.__get_challenge()
        captcha_id = captcha_challenge["data"]["id"]
        tip_y = captcha_challenge["data"]["question"]["tip_y"]
        solve_info = self.__solve_captcha(
            captcha_challenge["data"]["question"]["url1"],
            captcha_challenge["data"]["question"]["url2"],
        )
        solve_info.update({"id": captcha_id, "tip": tip_y})
        return self.__post_captcha(solve_info)
