import requests
import traceback
import logging
import datetime
import time
import os
import shutil
import glob
from natsort import natsorted
import imagehash
from PIL import Image

import Creds
import ImageFilter
import ImageSpliter

smileys = [
    (":D", "happy"),
    (":)", "smiley"),
    (":p", "tongue"),
    (":(", "sad"),
    (";)", "wink"),
    ("B)", "cool"),
    (":@", "angry"),
    (":o", "shocked"),
    (":s", "confused"),
    (":|", "neutral"),
    (":/", "wondering"),
    ("<3", "heart")
]


def filename_to_smiley(filename):
    for symbol, name in smileys:
        if filename.startswith(name):
            return symbol
    return ""


def get_new_hackthis_web_session():
    sess = requests.session()
    sess.post("https://www.hackthis.co.uk/?login", data={"username": Creds.username, "password": Creds.password}, timeout=20)
    return sess


def get_captcha(web_session, outputPathName=None):
    web_session.get("https://www.hackthis.co.uk/levels/captcha/3", timeout=20)
    response = web_session.get("https://www.hackthis.co.uk/levels/extras/captcha4.php", timeout=20)
    if outputPathName is not None:
        with open(outputPathName, "wb") as fd:
            fd.write(response.content)
    else:
        with open("captcha.png", "wb") as fd:
            fd.write(response.content)


def make_clean():
    folder = 'guessdata'
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)


def log(strToLog):
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')
    print("[%s] %s" % (str(st), str(strToLog)), flush=True)


def get_user_solution(captchaName):
    while True:
        data = input("Please enter solution for '%s': " % (captchaName))
        if len(data) < 10:
            print("Value too short. Please inser all captcha chars!")
        else:
            return data.rstrip("\n\r")

def do_the_magic():
    dhash_digests = {}
    phash_digests = {}
    for letter_image in glob.glob("traindata/*.png"):
        dhash_digest = imagehash.dhash(Image.open(letter_image))
        phash_digest = imagehash.phash(Image.open(letter_image))
        letter = filename_to_smiley(os.path.basename(letter_image))
        dhash_digests[dhash_digest] = letter
        phash_digests[phash_digest] = letter

    solution = ""

    for letter_image in natsorted(glob.glob("guessdata/*.png")):
        if "captcha" in letter_image:
            continue

        min_distance = 0xFFFF
        letter = "?"

        img = Image.open(letter_image)
        digest = imagehash.dhash(img)
        for known_digest in dhash_digests:
            distance = digest - known_digest
            if distance < min_distance:
                min_distance = distance
                letter = dhash_digests[known_digest]

        digest = imagehash.phash(img)
        for known_digest in phash_digests:
            distance = digest - known_digest
            if distance < min_distance:
                min_distance = distance
                letter = phash_digests[known_digest]

        solution += (letter + " ")
    return solution


def main():
    # # Create a web session
    # log("Creating a new hackthis.co.uk web session...")
    # web_session = get_new_hackthis_web_session()
    #
    # # Clean guessdata directory
    # log("Cleaning up old files...")
    # make_clean()
    #
    # # Fetch a new captcha
    # log("Download new captcha...")
    # get_captcha(web_session, "guessdata/captcha.png")

    # Remove black background from image
    log("Cleaning up image...")
    ImageFilter.clean("guessdata/captcha.png", "guessdata/captcha_clean.png")

    # Split every char of the image
    log("Split image....")
    ImageSpliter.ImgSplit("guessdata/captcha_clean.png")

    # Recognize chars
    log("Solving image captcha...")
    solution = do_the_magic()

    log("Submitting solution: '%s' " % (solution))
    # response = web_session.post("https://www.hackthis.co.uk/levels/captcha/4", data={"answer": solution.replace(" ", "") }, timeout=20).content
    #
    # if "Incomplete" not in str(response):
    #     log("SUCCESS!")
    # else:
    #     log("FAILED!")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(traceback.format_exc())
