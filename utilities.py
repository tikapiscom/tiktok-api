import random
import time
import hashlib
from datetime import datetime as dt
from urllib.parse import urlencode

class Utils:
    @staticmethod
    def parse_set_cookie_headers(set_cookie_headers):
        cookies = {}
        if set_cookie_headers:
            cookie_headers = set_cookie_headers.split(", ")
            for cookie_header in cookie_headers:
                parts = cookie_header.split(";")
                if parts:
                    cookie = parts[0]
                    cookie_key_value = cookie.split("=")
                    if len(cookie_key_value) == 2:
                        key = cookie_key_value[0].strip()
                        value = cookie_key_value[1].strip()
                        if value:
                            cookies[key] = value
        return cookies
    
    @staticmethod
    def get_follow_endpoint(aid):
        if int(aid) == 1340:
            return "lite/v2/relation/follow/"
        else:
            return "aweme/v1/commit/follow/user/"
    
    @staticmethod
    def get_like_endpoint(aid):
        if int(aid) == 1340:
            return "lite/v2/item/digg/"
        else:
            return "aweme/v1/commit/item/digg/"
        
    @staticmethod
    def generate_random_password():
        length = random.randint(10, 16)  
        special_chars = "@+"  
        uppercase_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  
        lowercase_chars = "abcdefghijklmnopqrstuvwxyz"  
        digits = "0123456789"  
        password_chars = [random.choice(special_chars)]
        password_chars += [random.choice(uppercase_chars) for _ in range(random.randint(1, 3))]
        remaining_length = length - len(password_chars)
        password_chars += [random.choice(lowercase_chars + digits) for _ in range(remaining_length)]
        random.shuffle(password_chars)
        password = ''.join(password_chars)
        return password

        
    @staticmethod
    def domain_chose(cookie: str = None):
        domains = {
            "maliva": [
                "api16-normal-c-alisg.tiktokv.com",
                "api19-normal-c-alisg.tiktokv.com",
                "api21-normal-c-alisg.tiktokv.com",
                "api22-normal-c-alisg.tiktokv.com",
            ],
            "useast1a": [
                "api16-normal-c-useast1a.tiktokv.com",
                "api19-normal-c-useast1a.tiktokv.com",
                "api22-normal-c-useast1a.tiktokv.com"
            ],
            "useast2a": [
                "api16-normal-c-useast2a.tiktokv.com",
                "api19-normal-c-useast2a.tiktokv.com",
                "api21-normal-c-useast2a.tiktokv.com",
                "api22-normal-c-useast2a.tiktokv.com"
            ],
            "us": [
                "api16-normal-useast5.us.tiktokv.com",
                "api19-normal-useast5.us.tiktokv.com"
            ]
        }
        captcha_urls = [
            "verify-sg.tiktokv.com",
            "verification-va.byteoversea.com"
        ]
        if cookie:
            cookie_dict = Utils.parse_cookies(cookie)
            tt_target_idc = cookie_dict.get('tt-target-idc', None)
            if tt_target_idc and tt_target_idc in domains:
                domain_choices = domains[tt_target_idc]
            else:
                domain_choices = [domain for sublist in domains.values()
                                  for domain in sublist]
        else:
            domain_choices = [domain for sublist in domains.values()
                              for domain in sublist]
        login_url = random.choice(domain_choices)
        captcha_url = random.choice(captcha_urls)
        return {"domain": login_url, "captcha_domain": captcha_url}
    
    @staticmethod
    def parse_cookies(cookie_str):
        cookie_dict = {}
        items = cookie_str.split(';')
        for item in items:
            parts = item.strip().split('=')
            if len(parts) == 2:
                key, value = parts
                key = key.strip()
                value = value.strip()
                if key in cookie_dict:
                    if isinstance(cookie_dict[key], list):
                        cookie_dict[key].append(value)
                    else:
                        cookie_dict[key] = [cookie_dict[key], value]
                else:
                    cookie_dict[key] = value
        cookie_dict = {k: v for k, v in cookie_dict.items()
                       if v is not None and v != ''}
        return cookie_dict
    
    @staticmethod
    def _xor_tiktok(string):
        encrypted = [hex(ord(c) ^ 5)[2:] for c in string]
        return "".join(encrypted)

    @staticmethod
    def hashed_id(value):
        hashed_id = value + "aDy0TUhtql92P7hScCs97YWMT-jub2q9"
        type = "2" if "@" in value else "3"
        hashed_value = hashlib.sha256(hashed_id.encode()).hexdigest()
        return f"hashed_id={hashed_value}&type={type}"
    
    @staticmethod
    def strip_strings(item):
        if isinstance(item, str):
            return item.strip()
        elif isinstance(item, list):
            return [Utils.strip_strings(sub_item) for sub_item in item]
        elif isinstance(item, dict):
            return {key: Utils.strip_strings(value) for key, value in item.items()}
        else:
            return item

    @staticmethod
    def userAgent(dev_info):
        device_model_or_type = dev_info['device_model'] if 'device_model' in dev_info else dev_info.get('device_type', 'Unknown')
        build_id_part = f"; Build/{dev_info['build_id']}" if 'build_id' in dev_info and dev_info['build_id'] else ""
        return f"{dev_info['package_name']}/{dev_info['update_version_code']} (Linux; U; Android {dev_info['os_version']}; {dev_info['lang_k']}_{dev_info['lang_b']}; {dev_info['os_version']}; {device_model_or_type}{build_id_part})"
        
    @staticmethod
    def generate_query(dev_info, extra=None):
        if extra is None:
            extra = {}
        app_type = "ttn" if int(dev_info.get("aid", -1)) == 385522 else "normal"
        dev_info["app_type"] = app_type
        manifest_version_code = update_version_code = "-1" if app_type == "ttn" else dev_info.get("manifest_version_code", "-1")
        update_version_code = dev_info.get("update_version_code", "-1")

        time_ts = int(time.time())
        url_params = {
            "manifest_version_code": manifest_version_code,
            "_rticket": str(int(round(time_ts * 1000))),
            "current_region": dev_info.get("lang_b", ""),
            "app_language": dev_info.get("lang_k", ""),
            "app_type": dev_info.get("app_type", ""),
            "iid": dev_info.get("install_id", ""),
            "channel": "googleplay",
            "device_type": dev_info.get("device_model", ""),
            "language": dev_info.get("lang_k", ""),
            "locale": f'{dev_info.get("lang_k", "")}-{dev_info.get("lang_b", "")}',
            "resolution": dev_info.get("resolution", "").replace("x", "*"),
            "openudid": dev_info.get("openudid", ""),
            "update_version_code": update_version_code,
            "ac2": "wifi5g",
            "cdid": dev_info.get("cdid", ""),
            "sys_region": dev_info.get("lang_b", ""),
            "os_api": dev_info.get("os_api", ""),
            "timezone_name": dev_info.get("tz_name", "").replace("/", "%2F"),
            "dpi": dev_info.get("dpi", ""),
            "carrier_region": dev_info.get("lang_b", ""),
            "ac": "wifi",
            "device_id": dev_info.get("device_id", ""),
            "mcc_mnc": dev_info.get("mcc_mnc", ""),
            "os_version": str(dev_info.get("os_version", "")),
            "timezone_offset": dev_info.get("tz_offset", ""),
            "version_code": dev_info.get("version_code", ""),
            "app_name": dev_info.get("app_name", ""),
            "version_name": dev_info.get("app_version", ""),
            "device_brand": dev_info.get("device_brand", ""),
            "op_region": dev_info.get("lang_b", ""),
            "ssmix": "a",
            "device_platform": "android",
            "build_number": dev_info.get("app_version", ""),
            "region": dev_info.get("lang_b", ""),
            "aid": dev_info.get("aid", ""),
            "ts": str(time_ts),
        }

        if not url_params["iid"]:
            del url_params["iid"], url_params["device_id"]
        
        url_params.update(extra)
        query = urlencode(url_params, safe="%2F")
        return query.replace("/", "%2F").replace("+", "%20").replace("+", "%20").replace("+", "%20").replace("+", "%20")

    
    @staticmethod
    def generate_random_birthdate():
        current_year = dt.now().year
        birth_year = random.randint(current_year - 50, current_year - 18)
        birth_month = random.randint(1, 12)
        if birth_month == 2:
            if (birth_year % 4 == 0 and birth_year % 100 != 0) or (birth_year % 400 == 0):
                max_day = 29
            else:
                max_day = 28
        elif birth_month in [4, 6, 9, 11]:
            max_day = 30
        else:
            max_day = 31
        birth_day = random.randint(1, max_day)
        return f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
