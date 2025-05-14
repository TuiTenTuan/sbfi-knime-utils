import os
import shutil

def clear_folder(path: str, clear_files: bool = True) -> None:
    """
    Clear all files in the specified folder or create it if it doesn't exist.
    
    Args:
        path (str): Path to the folder to clear or create.
        clear_files (bool): If True, delete all files and subdirectories in the folder. Defaults to True.
    
    Raises:
        ValueError: If the path is empty or not a directory.
        OSError: If the folder cannot be created or accessed.
    """
    if not path:
        raise ValueError("Path cannot be empty")
    
    # Create the folder if it doesn't exist
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create folder '{path}': {e}")
    
    # Verify it's a directory
    if not os.path.isdir(path):
        raise ValueError(f"Path '{path}' is not a directory")
    
    if clear_files:
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        except OSError as e:
            raise OSError(f"Failed to clear folder '{path}': {e}")