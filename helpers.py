
from cryptography.fernet import Fernet
from flask import redirect, request, session
from functools import wraps
import os
import pytesseract
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
try:
    from PIL import Image
except ImportError:
    import Image
import pyheif


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
    print("get pw")
    key = request.cookies.get("key")
    key.encode()
    f = Fernet(key)
    print("get pw middle")
    decrypted = f.decrypt(enc_cpw)
    cpw = decrypted.decode("utf-8")
    print("get pw end")
    return cpw


def activate_test(email, decrypted, barcode, acc_num):
    print("activate_test called")
    return False
    # https://www.youtube.com/watch?v=rfdNIOYGYVI&t=1114s
#     op = webdriver.ChromeOption()
#     op.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
#     op.add_argument("--headless")
#     op.add_argument("--no-sandbox")
#     op.add_argument("--disable-dev-sh-usage")
#     driver = webdriver.Chrome(executable_path=os.environ.get(
#         "CHROMEDRIVER_PATH"), chrome_options=op)
    driver = webdriver.Chrome(
        executable_path=os.environ.get("CHROMEDRIVER_PATH"))
    DELAY = 3
    POLL_FREQUENCY = .2
    driver.get("https://home.color.com/sign-in?next=%2Fcovid%2Factivation")
    driver.find_element_by_name("email").send_keys(email)
    driver.find_element_by_name("password").send_keys(decrypted)
    # login
    login_bt = "//span[@class='MuiButton-label']"
    driver.find_element_by_xpath(login_bt).click()

    # new page
    # select person
    person_bt = "//button[@class='MuiButtonBase-root MuiButton-root MuiButton-outlined jss268 MuiButton-outlinedPrimary']"
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.XPATH, person_bt)))
    except TimeoutException:
        return False
    driver.find_element_by_xpath(person_bt).click()

    # new page
    # choose to activate
    activate_bt = "//a[@role='button']"
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.XPATH, activate_bt)))
    except TimeoutException:
        return False
    driver.find_element_by_xpath(activate_bt).click()

    # start survey
    start = "//span[@class='MuiButton-label']"
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.XPATH, start)))
    except TimeoutException:
        return False
    driver.find_element_by_xpath(start).click()

    # no symptoms
    no_symp_bt = "//button[@data-testid='No']"
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.XPATH, no_symp_bt)))
    except TimeoutException:
        return False
    driver.find_element_by_xpath(no_symp_bt).click()

    # continue
    cont_bt = "//span[contains(text(),'Continue')]"
    driver.find_element_by_xpath(cont_bt).click()

    # new page
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.NAME, "primaryConsentIsAccepted")))
    except TimeoutException:
        return False
    driver.find_element_by_name("primaryConsentIsAccepted").click()
    driver.find_element_by_name("additionalConsents[0]").click()
    driver.find_element_by_name("additionalConsents[1]").click()
    driver.find_element_by_name("additionalConsents[2]").click()

    # continue from checkboxes and demos
    submit = "//button[@type='submit']"
    driver.find_element_by_xpath(submit).click()

    # new page
    # wait for title of next page
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.XPATH, "//h1[@class='MuiTypography-root jss2 MuiTypography-h1']")))
    except TimeoutException:
        return False
    driver.find_element_by_xpath(submit).click()
    # wait for confirmation box
    conf_bt = "//button[@class='MuiButtonBase-root MuiButton-root MuiButton-contained MuiButton-containedPrimary']"
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.XPATH, "//h2[@class='MuiTypography-root jss2 MuiTypography-h3']")))
    except TimeoutException:
        return False
    driver.find_element_by_xpath(conf_bt).click()

    # new page
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.XPATH, "//img[@alt='Tube with barcode']")))
    except TimeoutException:
        return False
    # put in codes
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.XPATH, "//img[@alt='Tube with barcode']")))
    except TimeoutException:
        return False
    driver.find_element_by_name("kit_barcode").send_keys(barcode)
    driver.find_element_by_name("accession_number").send_keys(acc_num)

    # double confirmation
    # wait for
    cont_bt = "//span[contains(text(),'Continue')]"
    driver.find_element_by_xpath(cont_bt).click()
    # wait for confirmation box
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.XPATH, "//img[@class='SampleIdentifierConfirmationDialog_Image__1FC_H']")))
    except TimeoutException:
        return False
    # final popup box
    double_conf_bt = "//span[normalize-space()='Confirm and Continue']"
    driver.find_element_by_xpath(double_conf_bt).click()
    print("So far so good...")

    # new page
    # see if color is happy
    try:
        WebDriverWait(driver, DELAY, poll_frequency=POLL_FREQUENCY).until(
            EC.presence_of_element_located((By.CLASS_NAME, "jss2")))
    except TimeoutException:
        return False
    if driver.find_element_by_class_name("jss2").get_attribute("innerHTML") == "You’ve activated your kit! Now, collect a sample.":
        return True
    return False
