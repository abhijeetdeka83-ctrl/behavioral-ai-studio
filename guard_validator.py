import os

def validate_file_spec(file_path: str, max_mb: float = 5.0, allowed_extensions: list = None) -> bool:
    """
    Validates file existence, enforces strict extension checks, 
    and verifies the file size doesn't exceed a specific Megabyte threshold.
    
    Args:
        file_path (str): The local system path to the temporary file cache.
        max_mb (float): Maximum allowed file size limit in Megabytes.
        allowed_extensions (list): List of permitted file extensions.
        
    Raises:
        ValueError: If the file breaks size limits or format rules.
        
    Returns:
        bool: True if the file successfully passes all structural criteria.
    """
    if allowed_extensions is None:
        # Default security profile optimized for authors' lore tracking and document templates
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.pdf']

    # 1. Verification of Existence
    if not os.path.exists(file_path):
        raise ValueError("The uploaded file could not be found or was corrupted during transfer.")

    # 2. Extension Verification
    # Split the extension from the path and normalize it to lowercase
    _, file_ext = os.path.splitext(file_path)
    normalized_ext = file_ext.lower()
    clean_allowed = [ext.lower() for ext in allowed_extensions]

    if normalized_ext not in clean_allowed:
        raise ValueError(
            f"Unauthorized file format '{file_ext}'. "
            f"Stratagem boundaries only permit: {', '.join(allowed_extensions)}"
        )

    # 3. File Size Verification
    file_size_bytes = os.path.getsize(file_path)
    max_bytes = max_mb * 1024 * 1024  # Explicit conversion to byte units

    if file_size_bytes > max_bytes:
        # Format the actual size nicely for the red UI error modal
        actual_mb = round(file_size_bytes / (1024 * 1024), 2)
        raise ValueError(
            f"File volume anomaly. Your file is {actual_mb}MB, "
            f"which exceeds the strict workspace threshold of {max_mb}MB."
        )

    return True
    
