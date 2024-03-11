import requests
import json
import random
import traceback
import time

from utilities import Utils
from HTTPRequester import HTTPRequester


class TikApis:
    def __init__(self, **kwargs):
        API_KEY = ''
        self.config = kwargs
        self.API_URL = "https://tikapis.com/api/android"
        self.DOMAIN_NORMAL = random.choice(["api-va.tiktokv.com"])
        self.headers = {'api-key': API_KEY, 'Content-Type': 'application/json'}
        self.proxy = self.config.get("proxy", "")
        self._setup_proxy()
        self.http_requester = HTTPRequester(
            proxies=self.proxy, app=self.config, API_URL=self.API_URL, API_HEADERS=self.headers)

    def _setup_proxy(self):
        proxy = self.proxy
        if proxy:
            proxy_type = "SOCKS5" if "socks5" in proxy.lower() else "HTTP"
            print(f"Using {proxy_type} proxy: {proxy}")
            return self.fetch_additional_data(proxy)
        else:
            print("No proxy provided. Using local network.")
            return self.fetch_additional_data()

    def fetch_additional_data(self, proxy=None):
        try:
            proxies = {'http': f'http://{proxy}',
                       'https': f'https://{proxy}'} if proxy else None
            response = requests.get(
                "https://ipinfo.io/json", proxies=proxies, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            print(response_data)
            country_code = response_data.get("country", "US")
            lang_k = "en" if country_code == "us" else country_code
            self.set_config(**{
                "tz_name": response_data.get("timezone", "America/New_York"),
                "lang_b": country_code,
                "lang_k": lang_k.lower(),
            })
        except Exception as e:
            traceback.print_exc()
            self.set_config(**{
                "tz_name": random.choice(["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"]),
                "lang_b": "US",
                "lang_k": "en",
            })

    def set_config(self, **kwargs):
        return self.config.update(kwargs)

    def error_check(self, response):
        if isinstance(response, dict) and 'error' in response:
            return response
        return None

    def payload_data(self, data):
        if not data:
            return ""
        elif isinstance(data, bytes):
            payload = data.decode()
            if payload.startswith('b\'') and payload.endswith('\''):
                return data
            elif payload.startswith('b"') and payload.endswith('"'):
                return data
            else:
                return data.hex()
        elif isinstance(data, str):
            try:
                parsed_data = json.loads(data)
                return json.dumps(parsed_data)
            except ValueError:
                return data
        else:
            try:
                return json.dumps(data)
            except ValueError:
                return data

    def session_cookie(self, response):
        if 'headers' in dir(response) and "set-cookie" in response.headers:
            set_cookie_header = response.headers.get("set-cookie", "")
            if set_cookie_header:
                cookies = Utils.parse_set_cookie_headers(set_cookie_header)
                existing_cookies = dict()
                if "cookie" in self.config:
                    existing_cookie_list = self.config["cookie"].split("; ")
                    for cookie in existing_cookie_list:
                        key_value = cookie.split("=")
                        if len(key_value) == 2:
                            existing_cookies[key_value[0].strip(
                            )] = key_value[1].strip()
                for key, value in cookies.items():
                    if not value:
                        continue
                    existing_cookies[key] = value
                new_cookie_string = "; ".join(
                    [f"{key}={value}" for key, value in existing_cookies.items()])
                self.config["cookie"] = new_cookie_string
                for key, value in cookies.items():
                    setattr(self, key, value)
        else:
            return

    def get_sign(self, url, data="", extra_headers={}):
        payload = {**self.config, "url": url,
                   "data": self.payload_data(data), "headers": json.dumps(extra_headers)}
        response = requests.post(
            f"{self.API_URL}/get_sign", headers=self.headers, json=payload)
        if response.status_code == 200:
            try:
                response_data = response.json()
                return response_data if 'X-Argus' in response_data else response.content
            except ValueError:
                return response.content
        return response.content

    def device_template(self):
        response = requests.post(
            f"{self.API_URL}/device_template", headers=self.headers, data=json.dumps(self.config))
        if response.status_code == 200:
            try:
                response_data = response.json()
                if 'package_name' in response_data:
                    return self.set_config(**response_data)
                else:
                    return response.content
            except ValueError:
                return response.content
        return response.content

    def check_and_convert(self, payload):
        if isinstance(payload, str):
            try:
                return bytes.fromhex(payload)
            except ValueError:
                return payload
        else:
            return payload


    def tiktok_auto_request(self, load):
        try:
            if "method" not in load:
                return json.dumps(load)
            if (load["method"] == "POST"):
                response = self.http_requester.post(
                    load["url"], headers=load["headers"], data=self.check_and_convert(load["payload"]))
                self.session_cookie(response)
                error = self.error_check(response)
                if error:
                    return error
                return response.content
            elif (load["method"] == "GET"):
                response = self.http_requester.get(
                    load["url"], headers=load["headers"])
                error = self.error_check(response)
                if error:
                    return error
                self.session_cookie(response)
                return response.content
            else:
                return json.dumps(load)
        except Exception as e:
            print({"error": str(e), "traceback": traceback.format_exc(), })
            return json.dumps(load)

    def api_request(self, endpoint, payload={}):
        response = requests.post(
            f"{self.API_URL}/{endpoint}", headers=self.headers, data=json.dumps({**payload, **self.config}))
        return response.json()

    def extract_ids(self, data):
        decoded_data = data.decode('utf-8')
        json_data = json.loads(decoded_data)
        self.set_config(**{
            "new_user": json_data.get("new_user"),
            "device_id": json_data.get("device_id_str"),
            "install_id": json_data.get("install_id_str"),
        })
        return self.set_config()

    def device_register(self):
        response = requests.post(
            f"{self.API_URL}/device_register", headers=self.headers, data=json.dumps(self.config))
        if response.status_code == 200:
            try:
                response_data = response.json()
                if 'method' in response_data:
                    self.extract_ids(self.tiktok_auto_request(response_data))
                else:
                    return response.content
            except ValueError:
                return response.content
        return response.content

    def get_token(self):
        response = requests.post(
            f"{self.API_URL}/get_token", headers=self.headers, data=json.dumps(self.config))
        if response.status_code == 200:
            try:
                response_data = response.json()
                if 'method' in response_data:
                    token = self.tiktok_auto_request(response_data)
                    tiktok_hex_token = {"hex": token.hex()}
                    get_token = self.api_request(
                        "get_token_decode", tiktok_hex_token)
                    if all(key in get_token for key in ["get_token"]):
                        return self.set_config(**get_token)
                else:
                    return response.content
            except ValueError:
                return response.content
        return response.content

    def get_seed(self):
        response = requests.post(
            f"{self.API_URL}/get_seed", headers=self.headers, data=json.dumps(self.config))
        if response.status_code == 200:
            try:
                response_data = response.json()
                if 'method' in response_data:
                    a = self.tiktok_auto_request(response_data)
                    tiktok_hex_token = {"get_hex": a.hex()}
                    get_token = self.api_request(
                        "get_seed_decode", tiktok_hex_token)
                    if all(key in get_token for key in ["ms_token", "p_x"]):
                        return self.set_config(**get_token)
                else:
                    return response.content
            except ValueError:
                return response.content
        return response.content

    def app_region(self, email):
        try:
            query = Utils.generate_query(self.config, {})
            payload = Utils.hashed_id(email)
            url = f"https://{self.DOMAIN_NORMAL}/passport/app/region/?{query}"
            headers = {
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "sdk-version": "2",
                "cookie": self.config.get("cookie", ""),
                "x-tt-token": self.config.get("x_token", ""),
                "x-bd-client-key": self.config.get("x_bd_lanusk", ""),
                'user-agent': Utils.userAgent(self.config)
            }
            headers.update(self.get_sign(url, payload, headers))
            json_response = self.http_requester.post(
                url, headers=headers, data=payload)
            if 'data' in json_response and 'domain' in json_response:
                self.session_cookie(json_response)
                return json_response.json()
            else:
                return json_response.json()
        except Exception as e:
            traceback.print_exc()

    def follow(self):
        extra = {"user_id": "107955", "sec_user_id": "", "type": "1"}
        domain = self.config.get(
            "domain", self.DOMAIN_NORMAL).replace("c-", "")
        end_point = Utils.get_follow_endpoint(self.config.get("aid", -1))
        domain = self.DOMAIN_NORMAL
        url = f"https://{domain}/{end_point}?{Utils.generate_query(self.config, extra)}"
        headers = ({
            "sdk-version": "2",
            "cookie": self.config["cookie"] if "cookie" in self.config else "",
            "x-tt-token": self.config["x_token"] if "x_token" in self.config else "",
            "x-bd-client-key": self.config["x_bd_lanusk"] if "x_bd_lanusk" in self.config else "",
            'user-agent': Utils.userAgent(self.config)
        })
        headers.update(self.get_sign(url, "", headers))
        response = self.http_requester.get(url, headers)
        error = self.error_check(response)
        if error:
            return error
        return response.content

    def digg(self):
        extra = {"aweme_id": "107955", "type": "1"}
        domain = self.config.get(
            "domain", self.DOMAIN_NORMAL).replace("c-", "")
        end_point = Utils.get_like_endpoint(self.config.get("aid", -1))
        domain = self.DOMAIN_NORMAL
        url = f"https://{domain}/{end_point}?{Utils.generate_query(self.config, extra)}"
        headers = ({
            "sdk-version": "2",
            "cookie": self.config["cookie"] if "cookie" in self.config else "",
            "x-tt-token": self.config["x_token"] if "x_token" in self.config else "",
            "x-bd-client-key": self.config["x_bd_lanusk"] if "x_bd_lanusk" in self.config else "",
            'user-agent': Utils.userAgent(self.config)
        })
        headers.update(self.get_sign(url, "", headers))
        response = self.http_requester.get(url, headers)
        error = self.error_check(response)
        if error:
            return error
        return response.content

    def account_register(self, email, password):
        app_region = self.app_region(email)
        print("app_region", app_region)
        if isinstance(app_region, bytes):
            app_region = app_region.decode('utf-8')

        if app_region and "data" in app_region and "domain" in app_region["data"]:
            domain_info = app_region["data"]
        else:
            domain_info = Utils.domain_chose(self.config.get("cookie", ""))

        self.captcha_domain = domain_info["captcha_domain"]
        self.DOMAIN_NORMAL = domain_info["domain"]
        extra = {
            "passport-sdk-version": self.config.get("passport_sdk_version", "19"),
            "uoo": "0",
            "cronet_version": self.config.get("cronet_version", ""),
            "ttnet_version": self.config.get("okhttp_version", ""),
            "use_store_region_cookie": "1"
        }
        query = Utils.generate_query(self.config, extra)
        payload = f"password={Utils._xor_tiktok(password)}&fixed_mix_mode=1&rules_version=v2&mix_mode=1&multi_login=1&email={Utils._xor_tiktok(email)}&account_sdk_source=app&birthday={Utils.generate_random_birthdate()}&multi_signup=0"
        url = f"https://{self.DOMAIN_NORMAL}/passport/email/register/v2/?{query}"
        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "sdk-version": "2",
            "cookie": self.config["cookie"] if "cookie" in self.config else "",
            "x-tt-token": self.config["x_token"] if "x_token" in self.config else "",
            "x-bd-client-key": self.config["x_bd_lanusk"] if "x_bd_lanusk" in self.config else "",
            'user-agent': Utils.userAgent(self.config)
        }
        headers.update(self.get_sign(url, payload, headers))
        r = self.http_requester.post(url, headers=headers, data=payload)
        error = self.error_check(r)
        if error:
            return error
        if hasattr(r, 'headers') and "x-tt-token" in r.headers and len(r.headers.get("x-tt-token", "")) > 0:
            response_json = r.json()
            set_cookie_headers = r.headers.get("x-tt-token")
            if set_cookie_headers:
                self.session_cookie(r)
                self.set_config(**{
                    "email": email,
                    "password": password,
                    "user": json.dumps(response_json.get("data")),
                    "x_token": r.headers.get("x-tt-token"),
                    "x_bd_lanusk": r.headers.get("x-bd-lanusk", ""),
                    "device_platform": "android",
                    "is_bot": 1,
                    **self.config,
                    "domain": self.DOMAIN_NORMAL,
                })
                time.sleep(2)
                print(self.follow())
                print(self.digg())
        else:
            return r.content


device = {
    "aid": "1233",
    "app_version": "33.7.3",
    "version_code": "330703",
    "manifest_version_code": "2023307030",
    "update_version_code": "2023307030",
    "sdk_ver": "v05.00.06-alpha.10-ov-android",
    # "proxy": "username:pass@host:port",
}


tik_api = TikApis(**device)
tik_api.device_template()
tik_api.device_register()
# tik_api.get_token()


print(json.dumps(tik_api.config))

# print("\n")

active_device = {
    "1": 'app_alert_check',
    # "2": 'log_settings',
    # "3": 'log_settings_2',
    # "4": 'report_mode_change_2',
    # "5": 'app_log',
    # "6": 'app_log_2',
    # "7": 'app_log_3',
    # "9": 'monitor_collect1',
    # "10": 'get_appmonitor_settings',
    # "3": 'monitor_collect',
    # "12": 'get_common',
    # "13": 'request_combine',
    # "14": 'check_in',
    # "15": 'store_region',
    # "16": 'trust_users',
    # "17": 'monitor_appmonitor',
    # "18": 'unificationprivacysettings',
    # "19": 'unificationsettingsrestriction',
    # "20": 'compliance_settings',
    # "21": 'policy_notice',
    # "22": 'cmpl_settings',
    # "23": "user_login_report",
    # "24": "user_login_logged",
    "25": "report_did_iid_update",
    # "26": "dyn_task",
    # "27": "get_dctoken",
    # "28": "report_image",
}
for key, value in active_device.items():
    api = tik_api.api_request(value)
    tiktok_auto_request = tik_api.tiktok_auto_request(api)
    print(f"Response: {value} -> value", {tiktok_auto_request})
    print("\n")

print("\n")

time.sleep(5)

account_register = tik_api.account_register(
    f"abcf{random.randint(5,999)}321313{random.randint(5,999)}fa@gmail.com", Utils.generate_random_password())
print("account_register", account_register)
print("\n")

print(json.dumps(tik_api.config))

