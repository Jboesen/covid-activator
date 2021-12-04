
from cryptography.fernet import Fernet
from flask import redirect, request, session
from functools import wraps
import os
import pytesseract
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
try:
    from PIL import Image
except ImportError:
    import Image
import pyheif
import glob


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def conv(image_path):
    # https://linuxtut.com/en/c2a85dced32c08aca209/
    new_name = image_path.replace("heic", "png")
    heif_file = pyheif.read(image_path)
    data = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    # "PNG"?
    data.save(new_name)


def ocr_core(filename):
    """
    This function will handle the core OCR processing of images.
    """
    # filename is a file obj
    # check for .heics
    split_tup = os.path.splitext(filename)
    # https://www.geeksforgeeks.org/how-to-get-file-extension-in-python/
    if split_tup[1] == ".heic":
        conv(filename)
        # delete original .heic
        os.remove(filename)
        filename = split_tup[0] + ".png"
    text = pytesseract.image_to_string(Image.open(
        filename))  # We'll use Pillow's Image class to open the image and pytesseract to detect the string in the image
    # delete new file
    os.remove(filename)
    return text


def get_pw(enc_cpw):
    key = request.cookies.get("key")
    key.encode()
    f = Fernet(key)
    decrypted = f.decrypt(enc_cpw)
    cpw = decrypted.decode("utf-8")
    return cpw


def activate_test(email, decrypted, barcode, acc_num):
    try:
        driver = webdriver.Chrome("/usr/bin/chromedriver")
        print("Successfully set Chrome to webdriver...")
        driver.get("https://home.color.com/sign-in?next=%2Fcovid%2Factivation")
        driver.find_element_by_name("email").send_keys(email)
        driver.find_element_by_name("password").send_keys(decrypted)
        # can I just plug in all these class elements?
        login_bt_cls = "MuiButtonBase-root MuiButton-root MuiButton-contained MuiButton-containedPrimary MuiButton-containedSizeLarge MuiButton-sizeLarge MuiButton-fullWidth"
        driver.find_element_by_class_name(login_bt_cls).click()
        person_bt_cls = "MuiButtonBase-root MuiButton-root MuiButton-outlined jss268 MuiButton-outlinedPrimary"
        driver.find_element_by_class_name(person_bt_cls).click()
        print("Successfully logged in...")

        start_bt_cls = "MuiButtonBase-root MuiButton-root MuiButton-contained MuiButton-containedPrimary Link_Link__2jUr8"
        driver.find_element_by_class_name(start_bt_cls).click()

        no_bt_cls = "QuizChoice tl w-100 flex justify-between bg-white pointer hover-opacity-0-75"
        driver.find_element_by_class_name(no_bt_cls).click()

        cont_bt_cls = "MuiButtonBase-root MuiButton-root MuiButton-contained ActionButtons_NextButton__MEOPx MuiButton-containedPrimary MuiButton-containedSizeLarge MuiButton-sizeLarge"
        driver.find_element_by_class_name(cont_bt_cls).click()

        driver.find_element_by_name("primaryConsentIsAccepted").click()
        driver.find_element_by_name("additionalConsents[0]").click()
        driver.find_element_by_name("additionalConsents[1]").click()
        driver.find_element_by_name("additionalConsents[2]").click()

        cont_bt_cls2 = "MuiButtonBase-root MuiButton-root MuiButton-contained MuiButton-containedPrimary MuiButton-containedSizeLarge MuiButton-sizeLarge"
        driver.find_element_by_class_name(cont_bt_cls2).click()

        driver.find_element_by_class_name(cont_bt_cls2).click()
        conf_cont_bt_cls = "MuiButtonBase-root MuiButton-root MuiButton-contained MuiButton-containedPrimary"
        driver.find_element_by_class_name(conf_cont_bt_cls).click()

        driver.find_element_by_name("kit_barcode").send_keys(barcode)
        driver.find_element_by_name("accession_number").send_keys(acc_num)
        driver.find_element_by_class_name(cont_bt_cls2).click()
        driver.find_element_by_class_name(conf_cont_bt_cls).click()
        if driver.find_element_by_class_name("MuiTypography-root jss2 MuiTypography-h1").text == "You’ve activated your kit! Now, collect a sample.":
            return True
    except NoSuchElementException:
        return False
    return False
