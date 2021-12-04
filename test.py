from selenium import webdriver

op = webdriver.ChromeOption()
op.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
op.add("--headless")
op.add("--no-sandbox")
op.add("--disable-dev-sh-usages")
driver = webdriver.Chrome(executable_path=os.environ.get(
    "CHROMEDRIVER_PATH"), chrome_options=op)
