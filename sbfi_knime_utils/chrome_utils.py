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
    # Define common temporary file extensions to ignore initially
    temp_extensions = (".crdownload", ".tmp", ".part", "!ut")
    
    while True:
        candidate_filenames = []
        try:
            for f_name in os.listdir(folder_to_check):
                full_path = os.path.join(folder_to_check, f_name)
                if os.path.isfile(full_path):
                    # Check if it matches the target extension AND is not a known temporary file
                    if f_name.lower().endswith(f".{extension}") and \
                       not any(f_name.lower().endswith(temp_ext) for temp_ext in temp_extensions):
                        candidate_filenames.append(f_name)
        except OSError as e:
            if logger:
                logger.log("wait_download_file", f"Error listing directory {folder_to_check}: {e}", is_error=True)
            time.sleep(1) # Wait a bit before retrying
            waiting_time += 1 # Count this as part of waiting time
            if waiting_time >= max_waiting_download:
                if logger:
                    logger.log(
                        "wait_download_file",
                        f"Timeout waiting for download after error listing directory {folder_to_check} for {max_waiting_download} seconds",
                        is_error=True
                    )
                raise TimeoutError(f"Timeout waiting for download after error listing directory {folder_to_check}")
            continue

        stable_files_to_process_this_iteration = []
        if candidate_filenames:
            if logger:
                logger.log("wait_download_file", f"Found candidate files: {candidate_filenames}", is_error=False)

            for report_filename in candidate_filenames:
                downloaded_file_path = os.path.join(folder_to_check, report_filename)
                try:
                    initial_size = os.path.getsize(downloaded_file_path)
                    time.sleep(1.0) # Wait for 1 second for file to stabilize

                    if not os.path.exists(downloaded_file_path): # File might have been removed/renamed
                        if logger:
                            logger.log("wait_download_file", f"File {downloaded_file_path} disappeared during stability check.", is_error=False)
                        continue
                    current_size = os.path.getsize(downloaded_file_path)

                    if current_size > 0 and current_size == initial_size:
                        stable_files_to_process_this_iteration.append(report_filename)
                        if logger:
                            logger.log("wait_download_file", f"File {report_filename} (path: {downloaded_file_path}) is stable. Size: {current_size}", is_error=False)
                    else:
                        if logger:
                            log_msg = f"File {report_filename} (path: {downloaded_file_path}) not stable or empty. " \
                                      f"Initial size: {initial_size}, current size: {current_size}. Will re-check."
                            logger.log("wait_download_file", log_msg, is_error=False)
                except FileNotFoundError:
                    if logger:
                        logger.log("wait_download_file", f"File {report_filename} (path: {downloaded_file_path}) not found during stability check.", is_error=False)
                except OSError as e:
                    if logger:
                        logger.log("wait_download_file", f"Error checking stability for {report_filename} (path: {downloaded_file_path}): {e}", is_error=True)
            
        if stable_files_to_process_this_iteration:
            if logger:
                logger.log(
                    "wait_download_file",
                    f"Processing stable files: {stable_files_to_process_this_iteration}",
                    is_error=False
                )
            
            for path_file_report in stable_files_to_process_this_iteration: # path_file_report is now just the filename
                downloaded_file_path = os.path.join(folder_to_check, path_file_report)

                if not os.path.exists(downloaded_file_path): # Re-check existence before move
                    if logger:
                        logger.log("wait_download_file", f"File {downloaded_file_path} disappeared before move. Skipping.", is_error=False)
                    continue

                filename_base, ext_with_dot = os.path.splitext(path_file_report)
                downloaded_file_name = filename_base.lower()
                downloaded_file_extension = ext_with_dot.lstrip('.').lower()
                                
                new_file_name = replace_filename if replace_filename else downloaded_file_name
                if replace_filename: # Ensure replace_filename is just a name, not a path
                    new_file_name = os.path.basename(new_file_name)

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
            # All stable files found in this pass have been processed
            return output_file
        
        # If no stable files were processed, continue polling
        waiting_time += 0.2
        if waiting_time >= max_waiting_download:
            if logger:
                logger.log(
                    "wait_download_file",
                    f"Timeout waiting for download after {max_waiting_download} seconds. No stable files found.",
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
    enable_incognito: bool = True,
    logger: Optional[Logger] = None
) -> WebDriver:
    """
    Create a Selenium Chrome WebDriver with customized options for downloads.
    
    Args:
        download_dir (str, optional): Directory for downloaded files.
        headless (bool): Run Chrome in headless mode if True. Defaults to True.
        clear_download_dir (bool): Clear the download directory if True. Defaults to True.
        disable_web_security (bool): Disable web security if True. Defaults to False.
        domain_skip_security (List[str], optional): List of domains to skip web security checks.
        enable_incognito (bool): Enable incognito mode if True. Defaults to True.
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
    # Display and startup
    chrome_options.add_argument("--start-maximized")             # Start maximized (ignored in headless)
    chrome_options.add_argument("--window-size=1920x1080")       # Ensure fixed resolution for consistency
    chrome_options.add_argument("--kiosk-printing")              # Silent printing (if printing is needed)

    # Performance and stability
    chrome_options.add_argument("--no-sandbox")                  # Needed in many headless environments
    chrome_options.add_argument("--disable-dev-shm-usage")       # Avoid shared memory issues in containers
    chrome_options.add_argument("--disable-gpu")                 # Disable GPU (required for headless on some systems)
    chrome_options.add_argument("--disable-software-rasterizer") # Disable software rendering fallback

    # Privacy and security
    chrome_options.add_argument("--disable-extensions")          # Disable extensions
    chrome_options.add_argument("--disable-popup-blocking")      # Allow popups (prevent block issues)
    chrome_options.add_argument("--no-default-browser-check")    # Disable default browser checks
    chrome_options.add_argument("--no-first-run")                # Skip first run dialogs
    chrome_options.add_argument("--disable-notifications")       # Disable site notifications
    chrome_options.add_argument("--disable-default-apps")        # Disable Chrome default apps
    chrome_options.add_argument("--disable-background-networking") # Prevent background connections
    chrome_options.add_argument("--disable-sync")                # Disable Chrome sync
    chrome_options.add_argument("--disable-translate")           # Disable translate prompt

    # Anti-detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    if enable_incognito:
        chrome_options.add_argument("--incognito")
    
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
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
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
    
