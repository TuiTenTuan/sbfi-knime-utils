from sbfi_knime_utils.logger import Logger

def test_logger_log():
    logger = Logger()
    logger.log("test_func", "Test message", is_error=False)
    df = logger.get_log_dataframe()
    
    assert len(df) == 1
    assert df.iloc[0]["Function"] == "test_func"
    assert df.iloc[0]["Message"] == "Test message"
    assert df.iloc[0]["IsError"] is False

def test_empty_log():
    logger = Logger()
    df = logger.get_log_dataframe()
    
    assert len(df) == 0
    assert list(df.columns) == ["Date", "Function", "Message", "IsError"]