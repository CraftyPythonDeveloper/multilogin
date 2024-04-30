import requests
import hashlib
import time

from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import random
from itertools import cycle


MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER = "https://launcher.mlx.yt:45001/api/v1"
LOCALHOST = "http://127.0.0.1"
HEADERS = {
 'Accept': 'application/json',
 'Content-Type': 'application/json'
 }

# Email, password
USERNAME = ""
PASSWORD = ""

# Your folder id
FOLDER_ID = "da1ab5be-2a6e-4724-9215-e12373b5ed03"

# WORKSPACE_ID = "cfed69bd-a7c5-4c7c-ad82-642179b19341"


def random_sleep(min_=5, max_=15):
    """
    Sleep randomly between min_ and max_ seconds
    :param min_: lower limit to sleep
    :param max_: upper limit to sleep
    :return: True
    """
    time.sleep(random.randint(min_, max_))
    return True


def move_mouse_randomly(act):
    """
    Move mouse inside selenium randomly
    :param act: action chain instance
    :return: True
    """
    act.move_by_offset(random.randint(0, 100), random.randint(0, 100)).perform()
    return True


def signin(workspace_id=None) -> str:
    global USERNAME, PASSWORD, MLX_BASE
    payload = {
        'email': USERNAME,
        'password': hashlib.md5(PASSWORD.encode()).hexdigest()
    }

    r = requests.post(f'{MLX_BASE}/user/signin', json=payload)

    if r.status_code != 200:
        print(f'\nError during login: {r.text}\n')
    else:
        response = r.json()['data']
        token = response['token']

    if workspace_id:
        payload = {
            "workspace_id": workspace_id,
            "email": USERNAME,
            "refresh_token": response["refresh_token"]}

        r = requests.post(f'{MLX_BASE}/user/refresh_token', json=payload)

        if r.status_code != 200:
            print(f'\nError during login: {r.text}\n')
        else:
            response = r.json()['data']
            token = response['token']

    return token


def start_profile(profile_id) -> webdriver:
    global FOLDER_ID, HEADERS, MLX_LAUNCHER

    r = requests.get(f'{MLX_LAUNCHER}/profile/f/{FOLDER_ID}/p/{profile_id}/start?automation_type=selenium',
                     headers=HEADERS)

    response = r.json()

    if r.status_code != 200:
        print(f'\nError while starting profile: {r.text}\n')
    else:
        print(f'\nProfile {profile_id} started.\n')

    selenium_port = response.get('status').get('message')
    options = ChromiumOptions()
    options.page_load_strategy = 'none'         # make page load None
    driver = webdriver.Remote(command_executor=f'{LOCALHOST}:{selenium_port}', options=options)

    return driver


def stop_profile(profile_id, web_driver) -> bool:
    global HEADERS, MLX_LAUNCHER

    r = requests.get(f'{MLX_LAUNCHER}/profile/stop/p/{profile_id}', headers=HEADERS)

    if r.status_code != 200:
        print(f'\nError while stopping profile: {r.text}\n')
    else:
        print(f'\nProfile {profile_id} stopped.\n')

    try:
        web_driver.close()          # force close chrome
    except:
        pass

    return True


def create_profile():
    global FOLDER_ID, HEADERS, MLX_BASE
    create_profile_payload = {
        "browser_type": random.choice(["mimic"]),
        "folder_id": FOLDER_ID,
        "name": f"automation_profile_{random.randint(1, 10_00_00)}_{random.randint(1, 10_00_00)}",
        "os_type": "windows",
        "parameters": {
            "fingerprint": {},
            "flags": {
                "navigator_masking": "mask",
                "audio_masking": "natural",
                "localization_masking": "mask",
                "geolocation_popup": "prompt",
                "geolocation_masking": "mask",
                "timezone_masking": "mask",
                "graphics_noise": "natural",
                "graphics_masking": "mask",
                "webrtc_masking": "mask",
                "fonts_masking": "mask",
                "media_devices_masking": "natural",
                "screen_masking": "mask",
                "proxy_masking": "custom",
                "ports_masking": "mask"
            },
            "storage": {
                "is_local": True,
                "save_service_worker": None
            },
            "proxy": {
                "type": "socks5",
                "host": "gate.multilogin.com",
                "port": 1080,
                "username": "133458_cfed69bd_a7c5_4c7c_ad82_642179b19341_multilogin_com-country-any-sid-rixLHD1ZoJDI-filter-medium",
                "password": "bl3p4x6ld1"
            }
        },
        "type": "[Profile Form] Create"
    }

    url = f"{MLX_BASE}/profile/create"
    r = requests.post(url, json=create_profile_payload, headers=HEADERS)
    return r.json()["data"]["ids"]


def delete_profile(profile_id):
    global HEADERS, MLX_BASE
    delete_profile_payload = {"ids": profile_id, "permanently":False}
    response = requests.post(f"{MLX_BASE}/profile/remove", json=delete_profile_payload, headers=HEADERS)
    return response.json()["status"]["message"]


def main(url, wait=5, retry=0, cleanup=True, max_retry=3):
    print("Creating a new profile..")
    profile_id = create_profile()
    random_sleep()
    print(f"Created a new profile with id: {profile_id}, starting it..")
    driver = start_profile(profile_id[0])
    print(f"Opening url: {url}")
    action = ActionChains(driver)
    driver.get(url)

    status = False
    random_sleep()
    for i in range(5):
        random_sleep(3, 5)  # wait between 6 and 10 seconds on each check before clicking, adjust accordingly
        try:
            move_mouse_randomly(action)  # move mouse randomly on each check, Note: you won't see the pointer movement however the mouse tracking events will see it.
            driver.find_element(By.TAG_NAME, "button").click()
            status = True
            random_sleep(3, 5)
            break
        except:
            continue

    if not status:
        if retry > max_retry:
            print(f"Maximum retry attempted, skipping this url: {url}")
            return False
        print(f"Captcha Detected, retrying attempt {retry + 1}..")
        stop_profile(profile_id[0], driver)
        if cleanup:
            message = delete_profile(profile_id)
            print(message)
        time.sleep(1)
        # return main(url, retry=retry + 1)
        return False    # if captcha detected, move to next url

    print("Successfully clicked the button, closing the chrome.")
    random_sleep()
    stop_profile(profile_id[0], driver)
    if cleanup:
        message = delete_profile(profile_id)
        print(message)
    random_sleep()
    return True


if __name__ == "__main__":
    urls = ["https://x.bitads.ai/lvdp6ajqzb2xl/lvfeo3gebs9a1", "https://x.bitads.ai/lvdp6ajqzb2xl/lvff8tnv079cw",
            "https://x.bitads.ai/lty9sdtvcg55s/lvf1r1vahdvfz", "https://x.bitads.ai/lvdp6ajqzb2xl/lvf6ra7qj3sz2"]

    # Auth
    access_token = signin()
    HEADERS.update({"Authorization": f'Bearer {access_token}'})

    # Main
    for url in cycle(urls):     # iterate each url endlessly
        try:  # To make sure script does not stop.
            main(url)
        except KeyboardInterrupt:
            print("Received keyboard interrupt. stopping script..")
            break
        except Exception as e:  # fallback
            print(e)
            random_sleep()
            continue
