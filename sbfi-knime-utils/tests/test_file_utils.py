import pytest
import os
from sbfi_knime_utils.file_utils import clear_folder

def test_clear_folder(tmp_path):
    log_dir = tmp_path / "logs"
    file1 = log_dir / "log1.txt"
    file2 = log_dir / "log2.txt"
    subdir = log_dir / "subdir"
    
    os.makedirs(subdir, exist_ok=True)
    file1.write_text("test1")
    file2.write_text("test2")
    subdir.joinpath("subfile.txt").write_text("subtest")
    
    clear_folder(log_dir)
    
    assert os.path.exists(log_dir)
    assert not file1.exists()
    assert not file2.exists()
    assert not subdir.exists()

def test_clear_folder_no_clear(tmp_path):
    log_dir = tmp_path / "logs"
    file1 = log_dir / "log1.txt"
    
    os.makedirs(log_dir, exist_ok=True)
    file1.write_text("test1")
    
    clear_folder(log_dir, clear_files=False)
    
    assert os.path.exists(log_dir)
    assert file1.exists()

def test_clear_folder_invalid_path():
    with pytest.raises(ValueError, match="Path cannot be empty"):
        clear_folder("")