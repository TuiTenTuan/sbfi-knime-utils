import os
import time
import shutil
from typing import List
from typing import Optional
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from .logger import Logger
from .file_utils import clear_folder

def enable_download_headless(
    browser: WebDriver,
    download_dir: str,
    logger: Optional[Logger] = None
) -> None:
    """
    Configure a headless browser to allow file downloads to a specified directory.
    
    Args:
        browser (WebDriver): Selenium WebDriver instance (e.g., ChromeDriver).
        download_dir (str): Directory path for downloads.
        logger (Logger, optional): Logger instance for logging the action.
    
    Raises:
        ValueError: If download_dir is empty or not a directory.
        OSError: If download_dir cannot be created or accessed.
        WebDriverException: If the browser command fails.
    """
    if not download_dir:
        raise ValueError("Download directory cannot be empty")
    
    # Ensure download directory exists
    try:
        os.makedirs(download_dir, exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create download directory '{download_dir}': {e}")
    
    if not os.path.isdir(download_dir):
        raise ValueError(f"'{download_dir}' is not a directory")
    
    # Configure browser for downloads
    try:
        browser.command_executor._commands["send_command"] = (
            "POST",
            "/session/$sessionId/chromium/send_command"
        )
        params = {
            "cmd": "Page.setDownloadBehavior",
            "params": {"behavior": "allow", "downloadPath": os.path.abspath(download_dir)}
        }
        browser.execute("send_command", params)
    except Exception as e:
        raise Exception(f"Failed to configure browser for downloads: {e}")
    
    # Log the action
    if logger:
        logger.log("enable_download_headless", f"Enabled downloads to {download_dir}", is_error=False)

def wait_download_file(
    folder_to_check: str,
    extension: str,
    folder_storage: str,
    replace_filename: Optional[str] = None,
    max_waiting_download: int = 300,    
    logger: Optional[Logger] = None
) -> List[List[str]]:
    """
    Monitor a folder for files with a specified extension, move them to a storage folder, and log actions.
    
    Args:
        folder_to_check (str): Folder to monitor for downloaded files.
        extension (str): File extension to look for (e.g., 'pdf', '.pdf').
        folder_storage (str): Destination folder for moved files.
        max_waiting_download (int): Maximum seconds to wait for downloads.
        replace_filename (str, optional): New filename (without extension) for moved files.
        logger (Logger, optional): Logger instance for logging actions.
    
    Returns:
        List[List[str]]: List of [filename, filepath, extension] for processed files.
    
    Raises:
        ValueError: If folders or extension are invalid.
        OSError: If folder creation or file operations fail.
        TimeoutError: If no files are found within max_waiting_download seconds.
    """
    if not folder_to_check or not folder_storage:
        raise ValueError("Folder paths cannot be empty")
    if not extension:
        raise ValueError("Extension cannot be empty")
    
    extension = extension.lstrip('.').lower()
    
    try:
        os.makedirs(folder_to_check, exist_ok=True)
        os.makedirs(folder_storage, exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create folders: {e}")
    
    if not os.path.isdir(folder_to_check) or not os.path.isdir(folder_storage):
        raise ValueError("Invalid folder paths")
    
    output_file: List[List[str]] = []
    waiting_time = 0
    
    while True:
        path_file_reports = [
            f for f in os.listdir(folder_to_check)
            if os.path.isfile(os.path.join(folder_to_check, f)) and f.lower().endswith(f".{extension}")
        ]
        
        if path_file_reports:
            if logger:
                logger.log(
                    "wait_download_file",
                    f"Found downloaded files: {path_file_reports}",
                    is_error=False
                )
            
            for path_file_report in path_file_reports:
                downloaded_file_path = os.path.join(folder_to_check, path_file_report)
                downloaded_file_name, downloaded_file_extension = path_file_report.lower().rsplit(".", 1)
                
                new_file_name = replace_filename if replace_filename else downloaded_file_name
                output_file_path = os.path.join(folder_storage, f"{new_file_name}.{downloaded_file_extension}")
                
                try:
                    shutil.move(downloaded_file_path, output_file_path)
                    if logger:
                        logger.log(
                            "wait_download_file",
                            f"Moved file from {downloaded_file_path} to {output_file_path}",
                            is_error=False
                        )
                    
                    output_file.append([new_file_name, output_file_path, downloaded_file_extension])
                except OSError as e:
                    if logger:
                        logger.log(
                            "wait_download_file",
                            f"Failed to move file {downloaded_file_path}: {e}",
                            is_error=True
                        )
                    raise
                
                try:
                    if os.path.exists(downloaded_file_path):
                        os.remove(downloaded_file_path)
                        if logger:
                            logger.log(
                                "wait_download_file",
                                f"Removed file: {downloaded_file_path}",
                                is_error=False
                            )
                except OSError as e:
                    if logger:
                        logger.log(
                            "wait_download_file",
                            f"Failed to remove file {downloaded_file_path}: {e}",
                            is_error=True
                        )
            
            return output_file
        
        waiting_time += 0.2
        if waiting_time >= max_waiting_download:
            if logger:
                logger.log(
                    "wait_download_file",
                    f"Timeout waiting for download after {max_waiting_download} seconds",
                    is_error=True
                )
            raise TimeoutError("Timeout waiting for download")
        
        time.sleep(0.2)

def create_chrome_driver(
    download_dir: Optional[str] = None,
    headless: bool = True,
    clear_download_dir: bool = True,
    disable_web_security: bool = False,
    domain_skip_security: Optional[List[str]] = None,
    logger: Optional[Logger] = None
) -> WebDriver:
    """
    Create a Selenium Chrome WebDriver with customized options for downloads.
    
    Args:
        download_dir (str, optional): Directory for downloaded files.
        headless (bool): Run Chrome in headless mode if True. Defaults to True.
        clear_download_dir (bool): Clear the download directory if True. Defaults to True.
        disable_web_security (bool): Disable web security if True. Defaults to False.
        logger (Logger, optional): Logger instance for logging actions.
    
    Returns:
        WebDriver: Configured Chrome WebDriver instance.
    
    Raises:
        ValueError: If download_dir is empty or not a directory.
        OSError: If download_dir cannot be created or accessed.
        WebDriverException: If driver initialization fails.
    """
    if download_dir is None:
        download_dir = os.path.join(os.getcwd(), "data", "download")
    
    clear_folder(download_dir, clear_download_dir)

    if not os.access(download_dir, os.W_OK):
        raise OSError(f"Download directory '{download_dir}' is not writable")
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--kiosk-printing") 
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    if headless:
        chrome_options.add_argument("--headless=new")

    if disable_web_security:
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-features=BlockInsecurePrivateNetworkRequests")

        if domain_skip_security:
            for domain in domain_skip_security:
                if domain.startswith("http://") or domain.startswith("https://"):
                    origin = domain
                else:
                    origin = "http://" + domain
                chrome_options.add_argument(f"--unsafely-treat-insecure-origin-as-secure={origin}")
    
    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "profile.default_content_settings.popups": False,
        "plugins.always_open_pdf_externally": True,
        "pdfjs.disabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        if logger:
            logger.log(
                "create_chrome_driver",
                f"Created Chrome WebDriver with download directory {download_dir}",
                is_error=False
            )

        return driver
    except Exception as ex:
        if logger:
            logger.log(
                "create_chrome_driver",
                f"Failed to create Chrome WebDriver: {ex}",
                is_error=True
            )
        raise Exception(f"Failed to create Chrome WebDriver: {ex}")
    
