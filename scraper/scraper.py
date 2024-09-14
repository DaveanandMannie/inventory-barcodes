from time import sleep

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement


def driver_setup(email: str, password: str) -> WebDriver:
    """ Sets up the chrome driver and logs into prod"""
    options: Options = Options()
    options.add_argument('headless')
    options.add_argument('--window-size=1920x1080')
    driver: WebDriver = WebDriver(options=options)

    driver.get('https://odoo.printgeek.ca')
    email_box: WebElement = driver.find_element(By.ID, 'login')
    pass_box: WebElement = driver.find_element(By.ID, 'password')
    login_button: WebElement = driver.find_element(
        By.XPATH, "//button[@type='submit' and contains(text(), 'Log in')]"
    )
    email_box.send_keys(email)
    pass_box.send_keys(password)
    sleep(0.2)
    login_button.click()
    return driver

def _get_table(driver: WebDriver) -> WebElement:
    """
    Finds the element containg receipt line items
    It is a sperate func so the element can be refreshed
    """
    table: WebElement = driver.find_element(
        By.NAME, 'move_ids_without_package'
    )
    return table

def get_label_data(link: str, driver: WebDriver) -> list[list[str]]:
    """
    Ruturns receipt line items in same format as v1
    """
    driver.get(link)
    sleep(2)
    table_element: WebElement = _get_table(driver)
    pagers: list[WebElement] = table_element.find_elements(
        By.CLASS_NAME, 'o_pager_counter'
    )
    if pagers:
        pager: WebElement = pagers[0]
        limit: str = pager.find_element(By.CLASS_NAME, 'o_pager_limit').text
        input_span: WebElement = pager.find_element(
            By.CLASS_NAME, 'o_pager_value'
        )
        input_span.click()
        sleep(1)
        input: WebElement = pager.find_element(By.CLASS_NAME, 'o_pager_value')
        input.send_keys(Keys.CONTROL, 'a')
        input.send_keys(f'1-{limit}')
        input.send_keys(Keys.ENTER)
        table_element = _get_table(driver)

    table: WebElement = table_element.find_element(By.TAG_NAME, 'tbody')
    rows: list[WebElement] = table.find_elements(By.TAG_NAME, 'tr')
    label_data: list[list[str]] = [['Product', 'Quantity']]
    for row in rows:
        temp_list: list[str] = []
        semi_parsed: list[str] = row.text.split(')')
        temp_list.append(semi_parsed[0] + ')')
        temp_list.append(semi_parsed[1].split(' ', maxsplit=2)[1])
        label_data.append(temp_list)
    return label_data

def get_reference(driver: WebDriver) -> str:
    """
    returns the reference number on the receipt
    """
    ref: str = driver.find_element(By.NAME, 'name').text
    clean_ref: str = ref.replace('/', '-')
    return clean_ref

