import os
import re
import sys
import time
import threading
import requests
import atexit
import signal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import tkinter as tk
from tkinter import filedialog

def clear_terminal():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def sanitize_filename(s):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', s)

def get_full_quality_url(url):
    match = re.search(r"(https://pbs.twimg.com/media/[^?]+)", url)
    if not match:
        return url 
    base = match.group(1)
    parts = base.rsplit('.', 1)
    if len(parts) == 2:
        filename, ext = parts
        if '_' in filename:
            filename = filename.split('_')[0]
        base = f"{filename}.{ext}"
    ext = base.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'gif']:
        ext = 'jpg'  # fallback
    return f"{base}?format={ext}&name=orig"

def create_filename(media_url, author_handle, tweet_date, media_type):
    media_id_match = re.search(r"/media/([^.?]+)", media_url)
    media_id = media_id_match.group(1) if media_id_match else 'media'
    ext = media_url.split('.')[-1].split('?')[0]
    ext = ext if ext in ['jpg', 'png', 'gif', 'jpeg', 'mp4'] else media_type
    return f"{tweet_date}_@{sanitize_filename(author_handle)}_{media_id}.{ext}"

def download_media(url, filename, download_folder, retries=3, backoff=2):
    filepath = os.path.join(download_folder, filename)
    if os.path.exists(filepath):
        return False
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            with open(filepath, 'wb') as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    out_file.write(chunk)
            return True
        except requests.HTTPError as e:
            if e.response.status_code == 404 and 'format=jpg' in url:
                # Retry with PNG if JPG not found
                png_url = url.replace('format=jpg', 'format=png')
                png_filename = filename.rsplit('.', 1)[0] + '.png'
                print(f"JPG not found. Retrying as PNG: {png_url}")
                return download_media(png_url, png_filename, download_folder)
            else:
                attempt += 1
                print(f"Failed to download {url}: {e}")
                if attempt < retries:
                    print(f"Retrying in {backoff} seconds... (Attempt {attempt + 1}/{retries})")
                    time.sleep(backoff)
                else:
                    print("Giving up. :(")
        except requests.RequestException as e:
            attempt += 1
            print(f"Failed to download {url}: {e}")
            if attempt < retries:
                print(f"Retrying in {backoff} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(backoff)
            else:
                print("Giving up. :(")
    return False

def pick_folder_dialog(prompt="Select folder"):
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title=prompt, initialdir="C:/")
    root.destroy()
    return folder_path

def pick_file_dialog(prompt="Select file", filetypes=None):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title=prompt, filetypes=filetypes, initialdir="C:/")
    root.destroy()
    return file_path

def pick_file_dialog_with_default(prompt="Select file", filetypes=None, default_dir=None):
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    if default_dir and not os.path.exists(default_dir):
        default_dir = "C:/Program Files/"
    path = filedialog.askopenfilename(title=prompt, filetypes=filetypes, initialdir=default_dir)
    root.destroy()
    return path

def main():
    clear_terminal()

    global stop_requested
    stop_requested = False

    global watermark
    watermark = "\n        00000000                                                                            \n             00000000       0000                  000        0000000000000                  \n                 0000         0000000         00000000000                0000000            \n                 0000           0000000   00000      000000                  00000          \n                 0000               00000000             00000                 0000         \n                 0000                                    00000      00000        00         \n                 0000                                  00000      000000000      000        \n                 0000                                00000        000   000     000         \n                 0000000                            0000          0000000      0000         \n                  000000000000000                 0000                        0000          \n                              000               000                        00000            \n                              000             0000            00      0000000               \n                              000           0000            000000000000                    \n                              000         0000             00000                            \n                               00       000000           00000                              \n                                       00000            0000                                \n                       0000         000000            00000                                 \n                        0000000   000000            000000                                  \n                            000000000     0000000  0000                                     \n                                                000000                                      "
    print(f"{watermark}\n\n=== WELCOME TO THE TWITTER MEDIA LIKES DOWNLOADER v1.101 ===\n\nThanks for using this tool! ^^\n\nThis Python script uses ChromeDriver and Selenium with Chrome/Brave to bulk-download all pieces of media from your Twitter likes, in the highest quality possible.\n*Keep in mind that gifs will NOT be downloaded as gifs but rather in video form to preserve quality.*\n\n")

    default_brave_dir = "C:/Program Files/BraveSoftware/Brave-Browser/Application"

    print("To begin, select your browser of choice:\n1 - Chrome\n2 - Brave")
    while True:
        browser_choice = input("Enter 1 for Chrome or 2 for Brave: ").strip()
        if browser_choice in ('1', '2'):
            break
        print("Please enter 1 or 2.")

    if browser_choice == '1':  # Chrome
        brave_path = None
        print("Using Chrome. Assuming default installation and no need to select browser executable.")
    elif browser_choice == '2':  # Brave
        default_brave_dir = "C:/Program Files/BraveSoftware/Brave-Browser/Application"
        print("Please select your Brave browser executable:")
        brave_path = pick_file_dialog_with_default(
            "Select Brave Executable", 
            [("Executables", "*.exe")], 
            default_dir=default_brave_dir
        )
        if not brave_path:
            print("No Brave executable selected, exiting. :/")
            sys.exit()

    print("\nSelect your ChromeDriver executable:")
    chromedriver_path = pick_file_dialog("Select ChromeDriver Executable", [("Executables", "*.exe")])
    if not chromedriver_path:
        print("No ChromeDriver executable selected, exiting. :/")
        sys.exit()

    print("\nFinally, select the folder where media will be saved:")
    download_folder = pick_folder_dialog("Select Download Folder")
    if not download_folder:
        print("No download folder selected, exiting. :/")
        sys.exit()

    options = Options()
    if browser_choice == '2':  # Brave
        options.binary_location = brave_path

    options.add_argument("--disable-usb-keyboard-detect")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])


    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    def cleanup(): # idk if this works
        try:
            driver.quit()
            print("Browser closed.")
        except:
            pass

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))  # Ctrl+C
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))  # kill

    print("\nI have now opened a new browser window. Please login to your Twitter account through this, and *DO NOT* touch this window afterwards! I will do the work for you :3")

    print("Waiting for login... Please complete login in the opened browser window. >_>")
    driver.get("https://x.com/login")

    while True:
        try:
            try:
                if "x.com/home" in driver.current_url:
                    break
            except Exception:
                print("Browser window was closed. Exiting. :/")
                driver.quit()
                sys.exit()
            time.sleep(1.5)

        except (WebDriverException):
            print("Browser window was closed. Exiting. :/")
            driver.quit()
            sys.exit()

    while True:
        username = input("\nLogin has been detected!\n\nI'm bad at reading, so please enter your Twitter username here (without @): ").strip()
        if not username:
            print("You must enter a username! >:(")
            continue
        yn = input(f"Is '{username}' correct? (Y/N): ").strip().lower()
        if yn == 'y':
            break
        else:
            print("Try again!")

    print(f"\nUsing username: {username}\n")

    while True:
        max_scrolls_str = input("The system I use to search through your likes is by scrolling down until I reach the maximum scroll limit. Please set a maximum scroll amount! (ENTER for no limit): ").strip()
        if max_scrolls_str == "":
            max_scrolls = 0
            break
        elif max_scrolls_str.isdigit():
            max_scrolls = int(max_scrolls_str)
            break
        else:
            print("Please enter a valid number or just press ENTER for no limit.")

    stop_tweet_id = None

    while True:
        yn = input("\nDo you want to stop scrolling when a specific tweet is reached? (Y/N): ").strip().lower()
        if yn == 'y':
            tweet_url = input("Enter the full URL of the tweet you want to stop at: ").strip()
            match = re.search(r"/status/(\d+)", tweet_url)
            if match:
                stop_tweet_id = match.group(1)
                print(f"Okay! Will stop when tweet ID {stop_tweet_id} is reached. :>")
            else:
                print("Please try again. >:(")
                continue
            break
        elif yn == 'n':
            break
        else:
            print("Please answer with Y or N.")

    print("\n== DISCLAIMER! ==\nWhile I'm certain this is safe and undetectable, scraping is against Twitter's TOS - I am not responsible for anything that may happen when using this tool.\n"
          "\nPlease be mindful of your available storage while using this tool, as depending on your likes, this may take a while and eat up your storage! Make sure you also have a stable internet connection.\n"
          "\nPress ENTER to confirm and start!")
    input()

    driver.get(f"https://x.com/{username}/likes")
    time.sleep(2)

    downloaded = set()
    total_downloaded = 0
    total_media_attempts = 0
    failed_tweets = 0
    start_time = time.time()

    def wait_for_enter():
        global stop_requested
        input("Press ENTER anytime to stop downloading...\n\n")
        stop_requested = True

    threading.Thread(target=wait_for_enter, daemon=True).start()

    max_scrolls_val = max_scrolls if max_scrolls > 0 else 10**9
    no_media_scrolls = 0
    max_no_media_scrolls = 20

    try:
        for i in range(max_scrolls_val):
            if stop_requested:
                print("Stop requested! Finishing downloads and exiting.")
                break

            if max_scrolls > 0:
                print(f"Scrolling... ({i+1}/{max_scrolls})\n")
            else:
                print(f"Scrolling... ({i+1})\n")

            media_this_scroll = 0

            tweets = driver.find_elements(By.XPATH, '//article[@role="article"]')

            for tweet in tweets:
                if stop_requested:
                    break

                if stop_tweet_id:
                    try:
                        status_link = tweet.find_element(By.XPATH, './/a[contains(@href, "/status/")]')
                        tweet_href = status_link.get_attribute('href')
                        if tweet_href and f"/status/{stop_tweet_id}" in tweet_href:
                            print(f"\nReached target tweet (ID: {stop_tweet_id}). Stopping scroll!")
                            stop_requested = True
                            break
                    except Exception as e:
                        print(f"Could not check tweet ID: {e}")

                try:
                    author_link = tweet.find_element(By.XPATH, './/a[contains(@href, "/") and not(contains(@href, "/status/"))]')
                    author_handle = author_link.get_attribute('href').split('/')[-1]

                    time_elem = tweet.find_element(By.TAG_NAME, 'time')
                    tweet_date = time_elem.get_attribute('datetime').split('T')[0]

                    imgs = tweet.find_elements(By.XPATH, './/img[contains(@src, "twimg.com/media/")]')
                    videos = tweet.find_elements(By.TAG_NAME, 'video')

                    for img in imgs:
                        src = img.get_attribute('src')
                        full_url = get_full_quality_url(src)
                        if full_url not in downloaded:
                            filename = create_filename(full_url, author_handle, tweet_date, 'jpg')
                            if download_media(full_url, filename, download_folder):
                                total_downloaded += 1
                                media_this_scroll += 1
                                print(f"> Downloaded! [{total_downloaded}]\n")
                            downloaded.add(full_url)
                            total_media_attempts += 1

                    for video in videos:
                        src = video.get_attribute('src')
                        if not src:
                            sources = video.find_elements(By.TAG_NAME, 'source')
                            src = sources[0].get_attribute('src') if sources else None
                        if src and src.startswith('https://video.twimg.com') and src not in downloaded:
                            filename = create_filename(src, author_handle, tweet_date, 'mp4')
                            if download_media(src, filename, download_folder):
                                total_downloaded += 1
                                media_this_scroll += 1
                                print(f"> Downloaded! [{total_downloaded}]\n")
                            downloaded.add(src)
                            total_media_attempts += 1

                except Exception as e:
                    print(f"Skipped a tweet due to error: {e}")
                    failed_tweets += 1

            if media_this_scroll == 0:
                no_media_scrolls += 1
                print(f"No media found this scroll. ({no_media_scrolls}/{max_no_media_scrolls})")
                if no_media_scrolls >= max_no_media_scrolls:
                    print(f"\nDetected {max_no_media_scrolls} consecutive scrolls with no media - I will assume that I've reached the bottom. Exiting!")
                    break
            else:
                no_media_scrolls = 0

            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(1.5)

    except WebDriverException:
        print("\nBrowser window was closed during scrolling. Exiting. :/")
        driver.quit()
        sys.exit()

    driver.quit()
    elapsed = time.time() - start_time
    print(f"\nDone! Total media downloaded: {total_downloaded}/{total_media_attempts}")
    if failed_tweets > 0:
        print(f"Skipped {failed_tweets} tweet(s) due to errors. :/")
    print(f"Time elapsed: {elapsed:.2f} seconds\n")

    try:
        if os.name == 'nt':  # Windows
            os.startfile(download_folder)
        elif sys.platform == 'darwin':  # macOS
            os.system(f'open "{download_folder}"')
        else:  # Linux
            os.system(f'xdg-open "{download_folder}"')
    except Exception as e:
        print(f"Could not open folder: {e}")

if __name__ == "__main__":
    main()
