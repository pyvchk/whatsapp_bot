import sys
import time
import datetime
import socket
import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
import smtplib
from configparser import ConfigParser
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from typing import NamedTuple


class ConfigData(NamedTuple):
    """Config.ini data class"""
    from_addr: str
    password: str
    to_addr: str
    wa_target: str
    wa_message: str
    wa_sending_time: str  # format HH:MM
    subject: str = 'QR_CODES'
    server: str = 'smtp.yandex.ru'
    port: int = 465
    wa_opening_time: int = 30
    html_waiting_time: float = 30
    qr_code_waiting: int = 60
    mail_text: str = "Script's maintainer: https://github.com/pyvchk"  # It is me


def cfg_parsing() -> ConfigData:
    """Config.ini parsing"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "config.ini")
    # trying to open `config.ini` and setting consts
    if os.path.exists(config_path):
        cfg = ConfigParser()
        cfg.read(config_path)
        cfg_data = ConfigData(from_addr=cfg.get("smtp",
                                                "email"
                                                ),
                              password=cfg.get("smtp",
                                               "passwd"
                                               ),
                              to_addr=cfg.get("smtp",
                                              "to_addr"
                                              ),
                              wa_target=cfg.get("wa",
                                                "wa_target"
                                                ),
                              wa_message=cfg.get("wa",
                                                 "wa_message"
                                                 ),
                              wa_sending_time=cfg.get("wa",
                                                      "sending_time"
                                                      ),
                              subject=cfg.get("smtp",
                                              "subject"
                                              ),
                              server=cfg.get("smtp",
                                             "server"
                                             ),
                              port=int(cfg.get("smtp",
                                               "port"
                                               )
                                       ),
                              wa_opening_time=int(cfg.get("wa",
                                                          "wa_opening_time"
                                                          )
                                                  ),
                              html_waiting_time=float(cfg.get("wa",
                                                              "html_waiting_time"
                                                              )
                                                      ),
                              qr_code_waiting=int(cfg.get("wa",
                                                          "qr_code_waiting"
                                                          )
                                                  ),
                              )
    else:
        print("Wrong config!")
        sys.exit()
    return cfg_data


def is_connected() -> bool:
    """Trying internet connection"""
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        os.system('echo Wrong Internet connection')
        raise OSError


def send_email(cfg_data: ConfigData, file_to_attach: str) -> None:
    """Email sending"""
    msg = MIMEMultipart()
    msg["From"] = cfg_data.from_addr
    msg["Subject"] = cfg_data.subject
    msg["Date"] = formatdate(localtime=True)
    if cfg_data.mail_text:
        msg.attach(MIMEText(cfg_data.mail_text))
    msg["To"] = cfg_data.to_addr

    # attachment - QR_CODE
    # opening and decoding
    attachment = MIMEBase('application', "octet-stream")
    header = 'Content-Disposition', f'attachment; filename="{file_to_attach}"'
    try:
        with open(file_to_attach, "rb") as fh:
            data = fh.read()
        attachment.set_payload(data)
        encoders.encode_base64(attachment)
        attachment.add_header(*header)
        msg.attach(attachment)
    except IOError:
        os.system(f'echo "Attachment opening error {file_to_attach}"')
    # sending...
    try:
        smtp = smtplib.SMTP_SSL(cfg_data.server, cfg_data.port)
        smtp.ehlo()
        smtp.login(cfg_data.from_addr, cfg_data.password)
        smtp.sendmail(cfg_data.from_addr, cfg_data.to_addr, msg.as_string())
        smtp.quit()
    except smtplib.SMTPException as err1:
        os.system('Something wrong with QR_CODE mailing...')
        raise err1


def qr_reader(cfg_data: ConfigData,
              driver: webdriver.Chrome) -> None:
    """ Shooting QR_CODE and sending on email """
    os.system(f'echo Wait {cfg_data.wa_opening_time} sec for QR_CODE on your email')
    #qr_path = '/app/screenshots/qr_code1.png'
    qr_path = '/home/pyvchk/PycharmProjects/pythonProject/screen/qr_code1.png'
    time.sleep(cfg_data.wa_opening_time)
    driver.save_screenshot(qr_path)
    send_email(cfg_data, qr_path)
    os.system(f'echo You have {cfg_data.qr_code_waiting} sec for QR_CODE validation')
    os.system(f'rm {qr_path}')
    time.sleep(cfg_data.qr_code_waiting)


def is_authorized(wait: WebDriverWait) -> bool:
    """For already authorized WA"""
    try:
        auth_xpath = '//div[@class="_2UwZ_"]'
        wait.until(ec.presence_of_element_located((
            By.XPATH, auth_xpath)))
        return False
    except TimeoutException:
        os.system('echo Already authorized')
    return True


def driver_init(cfg_data: ConfigData) -> WebDriverWait:
    """Opening Google Chrome and WA"""
    options = webdriver.ChromeOptions()
    # Options for docker container' Chrome
    #options.add_argument('--headless')
    #options.add_argument('--no-sandbox')
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64)"
                         " AppleWebKit/537.36 (KHTML, like Gecko)"
                         " Chrome/102.0.5005.61 Safari/537.36")
    #driver = webdriver.Chrome("/usr/local/bin/chromedriver",
    driver = webdriver.Chrome("/home/pyvchk/Загрузки/chromedriver_linux64/chromedriver",
                              options=options)
    driver.get("https://web.whatsapp.com/")
    wait = WebDriverWait(driver, cfg_data.html_waiting_time)
    driver.maximize_window()
    if not is_authorized(wait=wait):
        qr_reader(cfg_data=cfg_data, driver=driver)
    return wait


def wa_set(cfg_data: ConfigData, wait: WebDriverWait) -> WebElement:
    """Opening WA target chat and finding input box"""
    x_arg = '//span[contains(@title,' + cfg_data.wa_target + ')]'
    try:
        group_title = wait.until(ec.presence_of_element_located((
            By.XPATH, x_arg)))
        group_title.click()
    except TimeoutException as err2:
        os.system('echo Wrong WA_TARGET')
        raise err2
    inp_xpath = '//div[@class="_13NKt copyable-text selectable-text"][@data-tab="10"]'
    input_box = wait.until(ec.presence_of_element_located((
        By.XPATH, inp_xpath)))
    return input_box


def working():
    cfg_data = cfg_parsing()
    if is_connected():
        wait = driver_init(cfg_data=cfg_data)
        input_box = wa_set(cfg_data=cfg_data, wait=wait)
        while True:
            if datetime.datetime.now().strftime("%H:%M") == cfg_data.wa_sending_time:
                os.system('echo Messaging')
                try:
                    input_box.send_keys(cfg_data.wa_message + Keys.ENTER)
                except WebDriverException as err3:
                    os.system(
                        "echo Log out from WA because of problems with account's attaching")
                    raise err3
                os.system('echo See you tomorrow')
                time.sleep(85800)
            else:
                os.system('echo Send trying starts')
                time.sleep(60)


if __name__ == '__main__':
    working()
