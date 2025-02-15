import logging
import re
from datetime import datetime
from typing import Tuple

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger()


def get_saved_version() -> Tuple[str, int]:
    return 'https://www.legis.md/cautare/getResults?lang=ro&doc_id=', 108459


def save_new_version(url: str, new_version: int) -> None:
    pass


def find_latest_available_version(driver: WebDriver, page_url: str) -> int:
    driver.get(page_url)

    WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, 'response2')))

    years_list_block = driver.find_element(By.ID, 'block-years')
    if not years_list_block:
        raise Exception("No block-years found")

    years_list = years_list_block.find_elements(By.XPATH, './ul/li/a')
    if not years_list:
        raise Exception("block-years is empty")

    max_year_link = max(years_list, key=lambda x: int(x.text) if x.text.isnumeric() else -1)
    logger.info(f'Clicking on max_year_link: {max_year_link.text}')
    max_year_link.click()

    WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, 'response2')))

    changes_block = driver.find_element(By.ID, 'block-dates')
    if not changes_block:
        raise Exception("No block-dates found")

    all_changes = changes_block.find_elements(By.XPATH, './ul/li/a')
    if not all_changes:
        raise Exception("block-dates is empty")

    def max_f(x: WebElement):
        try:
            return datetime.strptime(x.text, '%d-%m-%Y').timestamp()
        except ValueError:
            return -1

    latest_change = max(all_changes, key=max_f)
    logger.info(f'Clicking on latest change: {latest_change.text}')
    latest_change.click()

    WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, 'response2')))

    regex_search = re.findall('doc_id=(\\d+)', driver.current_url)
    if not regex_search:
        raise Exception(f"No doc_id found in url: {driver.current_url}")

    doc_id = int(regex_search[0])

    return doc_id


def download_doc(doc_id: int) -> str:
    download_url = f'https://www.legis.md/cautare/downloadpdf/{doc_id}'
    filename = f'{doc_id}.pdf'

    logger.info(f'Downloading {doc_id} from: {download_url} into {filename}')

    download_request = requests.get(download_url, allow_redirects=True)
    open(filename, 'wb').write(download_request.content)

    return filename


def main():
    saved_url, saved_version = get_saved_version()
    page_url = f'{saved_url}{saved_version}'

    driver = webdriver.Firefox()
    latest_version = None
    try:
        latest_version = find_latest_available_version(driver, page_url)
    except Exception as e:
        logger.error(e)
    finally:
        driver.close()

    if latest_version is None:
        logger.info(f'No latest_version found. Exiting')
        return

    if latest_version <= saved_version:
        logger.info(f'Latest found version is smaller or equal to the last checked version. Exiting')
        return

    logger.info(f'Saving new version "{latest_version}" for url "{saved_url}')
    save_new_version(saved_url, latest_version)

    # Notify users of new version


if __name__ == '__main__':
    main()
