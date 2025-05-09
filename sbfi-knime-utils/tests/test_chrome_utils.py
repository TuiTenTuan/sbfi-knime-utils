import pytest
import os
from unittest.mock import Mock, patch
from sbfi_knime_utils import Logger, create_chrome_driver, enable_download_headless, wait_download_file

def test_create_chrome_driver_with_download_dir(tmp_path):
    download_dir = tmp_path / "downloads"
    logger = Logger()
    
    with patch("webdriver_manager.chrome.ChromeDriverManager.install", return_value="/mock/chromedriver"):
        with patch("selenium.webdriver.remote.webdriver.WebDriver.__init__", return_value=None) as mock_driver:
            driver = create_chrome_driver(str(download_dir), headless=True, logger=logger)
    
    assert os.path.exists(download_dir)
    assert driver is not None
    
    df = logger.get_log_dataframe()
    assert len(df) >= 2
    assert any(
        row["Message"].startswith("Created Chrome WebDriver") and row["Function"] == "create_chrome_driver"
        for _, row in df.iterrows()
    )
    assert any(
        row["Message"].startswith("Enabled downloads") and row["Function"] == "enable_download_headless"
        for _, row in df.iterrows()
    )

def test_create_chrome_driver_default_download_dir(tmp_path):
    logger = Logger()
    default_dir = os.path.join(os.getcwd(), "data", "download")
    
    with patch("webdriver_manager.chrome.ChromeDriverManager.install", return_value="/mock/chromedriver"):
        with patch("selenium.webdriver.remote.webdriver.WebDriver.__init__", return_value=None) as mock_driver:
            with patch("os.makedirs") as mock_makedirs:
                driver = create_chrome_driver(download_dir=None, headless=True, logger=logger)
    
    mock_makedirs.assert_called_with(default_dir, exist_ok=True)
    assert driver is not None
    
    df = logger.get_log_dataframe()
    assert len(df) >= 2
    assert any(
        row["Message"].startswith(f"Created Chrome WebDriver with download directory {default_dir}")
        for _, row in df.iterrows()
    )

def test_create_chrome_driver_invalid_dir(tmp_path):
    logger = Logger()
    invalid_dir = tmp_path / "not_a_dir"
    with open(invalid_dir, "w") as f:
        f.write("test")
    
    with pytest.raises(ValueError, match=f"'{invalid_dir}' is not a directory"):
        create_chrome_driver(str(invalid_dir), logger=logger)

def test_enable_download_headless(tmp_path):
    browser = Mock()
    browser.command_executor._commands = {}
    browser.execute = Mock(return_value=None)
    
    download_dir = tmp_path / "downloads"
    logger = Logger()
    
    enable_download_headless(browser, str(download_dir), logger)
    
    assert os.path.exists(download_dir)
    assert "send_command" in browser.command_executor._commands
    browser.execute.assert_called_with(
        "send_command",
        {
            "cmd": "Page.setDownloadBehavior",
            "params": {"behavior": "allow", "downloadPath": os.path.abspath(download_dir)}
        }
    )
    
    df = logger.get_log_dataframe()
    assert len(df) == 1
    assert df.iloc[0]["Function"] == "enable_download_headless"
    assert df.iloc[0]["Message"] == f"Enabled downloads to {download_dir}"
    assert df.iloc[0]["IsError"] is False

def test_enable_download_headless_no_logger(tmp_path):
    browser = Mock()
    browser.command_executor._commands = {}
    browser.execute = Mock(return_value=None)
    
    download_dir = tmp_path / "downloads"
    
    enable_download_headless(browser, str(download_dir))
    
    assert os.path.exists(download_dir)
    browser.execute.assert_called()

def test_enable_download_headless_invalid_dir():
    browser = Mock()
    with pytest.raises(ValueError, match="Download directory cannot be empty"):
        enable_download_headless(browser, "")

def test_wait_download_file(tmp_path):
    folder_to_check = tmp_path / "downloads"
    folder_storage = tmp_path / "storage"
    file_path = folder_to_check / "test.pdf"
    
    os.makedirs(folder_to_check, exist_ok=True)
    os.makedirs(folder_storage, exist_ok=True)
    file_path.write_text("test content")
    
    logger = Logger()
    
    with patch("os.listdir", return_value=["test.pdf"]):
        with patch("os.path.isfile", return_value=True):
            output_file = wait_download_file(
                str(folder_to_check),
                "pdf",
                str(folder_storage),
                max_waiting_download=5,
                replace_filename="new_test",
                logger=logger
            )
    
    assert os.path.exists(folder_storage / "new_test.pdf")
    assert not os.path.exists(file_path)
    assert output_file == [["new_test", str(folder_storage / "new_test.pdf"), "pdf"]]
    
    df = logger.get_log_dataframe()
    assert len(df) >= 2
    assert any(
        row["Message"].startswith("Found downloaded files") and row["Function"] == "wait_download_file"
        for _, row in df.iterrows()
    )
    assert any(
        row["Message"].startswith("Moved file") and row["Function"] == "wait_download_file"
        for _, row in df.iterrows()
    )

def test_wait_download_file_timeout(tmp_path):
    folder_to_check = tmp_path / "downloads"
    folder_storage = tmp_path / "storage"
    
    os.makedirs(folder_to_check, exist_ok=True)
    os.makedirs(folder_storage, exist_ok=True)
    
    logger = Logger()
    
    with patch("os.listdir", return_value=[]):
        with pytest.raises(TimeoutError, match="Timeout waiting for download"):
            wait_download_file(
                str(folder_to_check),
                "pdf",
                str(folder_storage),
                max_waiting_download=1,
                logger=logger
            )
    
    df = logger.get_log_dataframe()
    assert any(
        row["Message"].startswith("Timeout waiting") and row["IsError"]
        for _, row in df.iterrows()
    )

def test_wait_download_file_invalid_input():
    logger = Logger()
    
    with pytest.raises(ValueError, match="Folder paths cannot be empty"):
        wait_download_file("", "pdf", "storage", 5, logger=logger)
    
    with pytest.raises(ValueError, match="Extension cannot be empty"):
        wait_download_file("downloads", "", "storage", 5, logger=logger)