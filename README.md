# Knime Python Utils

This Python package provides a collection of utility functions designed to streamline workflow automation, especially when used in conjunction with KNIME. It includes features for creating and clearing folders, structured logging, and helpful tools for managing ChromeDriver operations in browser automation tasks. The package is lightweight and ideal for repetitive data processing pipelines or test automation scenarios where clean folder management and robust logging are essential.

## Features
- **Logging**: Log messages with timestamps, function names, and error status, exportable to a pandas DataFrame.
- **Folder Management**: Clear or create folders with robust error handling.
- **Browser Automation**: Configure Chrome WebDriver for headless or non-headless file downloads, with support for monitoring and moving downloaded files.
- **Extensibility**: Designed for easy integration into automation scripts with comprehensive logging.

## Installation
Install the package via pip:
```bash
pip install sbfi-knime-utils
```

### Requirements
- Python >= 3.8
- Dependencies: `pandas>=1.5.0`, `selenium>=4.0.0`, `webdriver_manager>=4.0.0`

## Usage Guidelines
### Basic Logging
Create a logger, log messages, and export logs to a pandas DataFrame:
```python
from sbfi_knime_utils.logger import Logger

# Initialize logger
logger = Logger()

# Log messages
logger.log("main", "Starting application")
logger.log("main", "Error occurred", is_error=True)

# Export logs to DataFrame
df = logger.get_log_dataframe()

knio.output_tables[2] = knio.Table.from_pandas(df)
```

### Folder Management
Clear or create a folder:
```python
from sbfi_knime_utils.file_utils import clear_folder

# Clear all files in a folder
clear_folder("logs")

# Create a folder without clearing existing files
clear_folder("logs", clear_files=False)
```

### Browser Automation
Set up a Chrome WebDriver for downloading files and monitor the download directory:
```python
from sbfi_knime_utils.logger import Logger
from sbfi_knime_utils.chrome_utils import create_chrome_driver, wait_download_file

# Initialize logger
logger = Logger()

# Create Chrome WebDriver with default download directory
browser = create_chrome_driver(logger=logger)  # Uses <cwd>/data/download

# Navigate to a download URL (example)
browser.get("https://example.com/sample.pdf")

# Wait for and process downloaded files
output_files = wait_download_file(
    folder_to_check="data/download",
    extension="pdf",
    folder_storage="storage",
    max_waiting_download=30,
    replace_filename="report",
    logger=logger
)
print(output_files)

# Clean up
browser.quit()
```

### Advanced Example
Combine logging, folder management, and browser automation:
```python
from sbfi_knime_utils.chrome_utils import create_chrome_driver, wait_download_file

# Initialize logger
logger = Logger()

# Clear download and storage directories
clear_folder("data/download")
clear_folder("storage")

# Create Chrome WebDriver with custom download directory
browser = create_chrome_driver(download_dir="custom_downloads", headless=True, logger=logger)

# Navigate to a page and trigger a download
browser.get("https://example.com/sample.pdf")

# Wait for and move the downloaded file
output_files = wait_download_file(
    folder_to_check="custom_downloads",
    extension="pdf",
    folder_storage="storage",
    max_waiting_download=30,
    replace_filename="sample_report",
    logger=logger
)

# Log results
logger.log("main", f"Processed files: {output_files}")

# Export logs
print(logger.get_log_dataframe())

# Clean up
browser.quit()
```

### Enable download when run in headless mode
Set up a Chrome WebDriver for downloading files and monitor the download directory:
```python
from sbfi_knime_utils.logger import Logger
from sbfi_knime_utils.chrome_utils import create_chrome_driver, wait_download_file, enable_download_headless

# Initialize logger
logger = Logger()

# Create Chrome WebDriver with default download directory
browser = create_chrome_driver(logger=logger)  # Uses <cwd>/data/download

# enable download before start download
enable_download_headless(browser)

# Navigate to a download URL (example)
browser.get("https://example.com/sample.pdf")

# Wait for and process downloaded files
output_files = wait_download_file(
    folder_to_check="data/download",
    extension="pdf",
    folder_storage="storage",
    max_waiting_download=30,
    replace_filename="report",
    logger=logger
)
print(output_files)

# Clean up
browser.quit()
```

## API Reference

### `Logger` Class
A utility for logging messages with timestamps and exporting logs to a pandas DataFrame.

#### `__init__()`
Initialize an empty logger.
- **Parameters**: None
- **Returns**: None

#### `log(function_name: str, message: str, is_error: bool = False) -> None`
Log a message with a timestamp, function name, and error status.
- **Parameters**:
  - `function_name` (str): Name of the function or context.
  - `message` (str): Log message content.
  - `is_error` (bool, optional): Indicates if the message is an error. Defaults to `False`.
- **Returns**: None
- **Example**:
  ```python
  logger = Logger()
  logger.log("main", "Task completed")
  ```

#### `get_log_dataframe() -> pd.DataFrame`
Return logged messages as a pandas DataFrame with columns `['Date', 'Function', 'Message', 'IsError']`.
- **Parameters**: None
- **Returns**: `pd.DataFrame` - DataFrame of logs, empty if no logs exist.
- **Example**:
  ```python
  df = logger.get_log_dataframe()
  print(df)
  ```

### `clear_folder(path: str, clear_files: bool = True) -> None`
Clear all files in a folder or create it if it doesn't exist.
- **Parameters**:
  - `path` (str): Path to the folder.
  - `clear_files` (bool, optional): If `True`, delete all files and subdirectories. Defaults to `True`.
- **Returns**: None
- **Raises**:
  - `ValueError`: If `path` is empty or not a directory.
  - `OSError`: If folder creation or clearing fails.
- **Example**:
  ```python
  clear_folder("logs")
  ```

### `create_chrome_driver(download_dir: Optional[str] = None, headless: bool = True, logger: Optional[Logger] = None) -> WebDriver`
Create a Selenium Chrome WebDriver configured for file downloads.
- **Parameters**:
  - `download_dir` (str, optional): Directory for downloads. If `None`, defaults to `<cwd>/data/download`.
  - `headless` (bool, optional): Run in headless mode if `True`. Defaults to `True`.
  - `clear_download_dir` (bool, optional): Clear download folder if `True`. Defaults to `True`.
  - `disable_web_security` (bool, optional): Disable web security if `True`. Allow access to the web run with `HTTP` or unsecure. `**BE CAREFULL!!**`. Defaults to `False`.
  - `domain_skip_security` (List[str], optional): List of domains to treat as secure (bypass insecure warnings). Defaults to `None`.
  - `logger` (Logger, optional): Logger instance for logging actions. Defaults to `None`.
- **Returns**: `WebDriver` - Configured Chrome WebDriver instance.
- **Raises**:
  - `ValueError`: If `download_dir` is not a directory.
  - `OSError`: If `download_dir` cannot be created.
  - `WebDriverException`: If driver initialization fails.
- **Example**:
  ```python
  browser = create_chrome_driver(download_dir="downloads", logger=logger)
  ```
  ```python
  browser = create_chrome_driver(download_dir="downloads", disable_web_security=True, domain_skip_security=["http://localhost.com"] logger=logger)
  ```

### `enable_download_headless(browser: WebDriver, download_dir: str, logger: Optional[Logger] = None) -> None`
Configure a headless Chrome WebDriver to allow file downloads.
- **Parameters**:
  - `browser` (WebDriver): Selenium WebDriver instance.
  - `download_dir` (str): Directory for downloads.
  - `logger` (Logger, optional): Logger instance for logging. Defaults to `None`.
- **Returns**: None
- **Raises**:
  - `ValueError`: If `download_dir` is empty or not a directory.
  - `OSError`: If `download_dir` cannot be created.
  - `WebDriverException`: If the browser command fails.
- **Example**:
  ```python
  enable_download_headless(browser, "downloads", logger)
  ```

### `wait_download_file(folder_to_check: str, extension: str, folder_storage: str, max_waiting_download: int, replace_filename: Optional[str] = None, logger: Optional[Logger] = None) -> List[List[str]]`
Monitor a folder for files with a specified extension, move them to a storage folder, and log actions.
- **Parameters**:
  - `folder_to_check` (str): Folder to monitor for downloads.
  - `extension` (str): File extension to look for (e.g., `'pdf'` or `'.pdf'`).
  - `folder_storage` (str): Destination folder for moved files.
  - `max_waiting_download` (int): Maximum seconds to wait for downloads.
  - `replace_filename` (str, optional): New filename (without extension) for moved files. Defaults to `None`.
  - `logger` (Logger, optional): Logger instance for logging. Defaults to `None`.
- **Returns**: `List[List[str]]` - List of `[filename, filepath, extension]` for processed files.
- **Raises**:
  - `ValueError`: If folders or extension are invalid.
  - `OSError`: If folder creation or file operations fail.
  - `TimeoutError`: If no files are found within `max_waiting_download` seconds.
- **Example**:
  ```python
  files = wait_download_file("downloads", "pdf", "storage", 300, "report", logger)
  ```

## Testing
The package includes a test suite using pytest. To run tests:
```bash
pip install pytest
pytest tests/
```

The test suite covers:
- Logger functionality (`test_logger.py`)
- Folder clearing (`test_utils.py`)
- Browser automation (`test_browser_utils.py`)
- Package imports and version (`test_init.py`)

## Contributing
1. Fork the repository: `https://github.com/TuiTenTuan/sbfi-knime-utils`
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m "Add feature"`
4. Push to the branch: `git push origin feature-name`
5. Open a pull request.

## License
MIT License. See [LICENSE](LICENSE) for details.

## Support
For issues or feature requests, open an issue on the [GitHub repository](https://github.com/TuiTenTuan/sbfi-knime-utils).