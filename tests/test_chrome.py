from sbfi_knime_utils.chrome_utils import create_chrome_driver
import pytest

def test_create_chrome_driver():
    # Test with default options
    driver = create_chrome_driver()
    assert driver is not None
    driver.quit()
