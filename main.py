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
from PIL import ImageFile

import Creds
import ImageFilter
import ImageSpliter

smileys = [
    (":D", 2000),
    (":)", 2027),
    (":p", 2369),
    (":(", 1474),
    (";)", 800),
    ("B)", 2700),
    (":@", 2633),
    (":o", 1758),
    (":s", 2250),
    (":|", 1859),
    (":/", 2061),
    ("<3", 3600)
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


def get_pixels_of_color(imagePath, color):
	# https://stackoverflow.com/questions/27868250/python-find-out-how-much-of-an-image-is-black
    with open(imagePath, "rb") as fd:
        p = ImageFile.Parser()
        p.feed(fd.read())
        image = p.close()
        w, h = image.size

        pixels_of_color = 0
        for x in range(0, w):
            for y in range(0, h):
                if image.getpixel((x, y)) == color:
                    pixels_of_color += 1
        return pixels_of_color


def zoom_in(imgIn, imgOut):
	basewidth = 2000
	img = Image.open(imgIn)
	wpercent = (basewidth/float(img.size[0]))
	hsize = int((float(img.size[1])*float(wpercent)))
	img = img.resize((basewidth,hsize), Image.ANTIALIAS)
	img.save(imgOut) 


def do_the_magic():
    solution = ""

    for letter_image in natsorted(glob.glob("guessdata/*.png")):
        if "captcha" in letter_image:
            continue
        black_pixels = get_pixels_of_color(letter_image, ImageFilter.BLACK)
        print("%s -> %d" % (letter_image, black_pixels) )

        # Look for the emoji with colest number of pixels to current letter image
        min_diff = 100
        closest_smiley = ""
        for smiley in smileys:
        	diff = 0
        	# Look for a closer smiley
        	if black_pixels > smiley[1]:
        		diff = black_pixels - smiley[1]
        	else:
        		diff = smiley[1] - black_pixels
        	
        	if diff < min_diff:
        		min_diff = diff
        		closest_smiley = smiley[0]
       	solution += (closest_smiley + ' ')

       	# print("%s -> %d closer to %s" % (letter_image, black_pixels, closest_smiley))

    return solution


def main():
    # Create a web session
    log("Creating a new hackthis.co.uk web session...")
    web_session = get_new_hackthis_web_session()
    
    # Clean guessdata directory
    log("Cleaning up old files...")
    make_clean()
    
    # Fetch a new captcha
    log("Download new captcha...")
    get_captcha(web_session, "guessdata/captcha.png")

    # Zoom in a pucture
    log("Zooming into image...")
    zoom_in("guessdata/captcha.png", "guessdata/captcha_zoomed.png")

    # Remove black background from image
    log("Cleaning up image...")
    ImageFilter.clean("guessdata/captcha_zoomed.png", "guessdata/captcha_clean.png")

    # Split every char of the image
    log("Split image....")
    ImageSpliter.ImgSplit("guessdata/captcha_clean.png")
    
    # # Recognize chars
    # log("Solving image captcha...")
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
