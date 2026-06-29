import os

# Cryptographic 'magic number' signatures that define authentic, valid file types
MAGIC_NUMBERS = {
    '.png':  [b'\x89PNG\r\n\x1a\n'],
    '.jpg':  [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\xff\xd8\xff\xe2', b'\xff\xd8\xff\xee'],
    '.jpeg': [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\xff\xd8\xff\xe2', b'\xff\xd8\xff\xee'],
    '.pdf':  [b'%PDF']
}

def inspect_binary_header(file_path: str) -> bool:
    """
    Opens a file stream in raw read-binary mode to verify that its internal 
    data structure matches its declared filename extension. 
    
    Args:
        file_path (str): The local path to the temporary file cache.
        
    Raises:
        ValueError: If the raw binary header does not match the expected signatures.
        
    Returns:
        bool: True if the file content is verified as safe and authentic.
    """
    if not os.path.exists(file_path):
        raise ValueError("Target file went missing from the processing buffer during quarantine.")

    # 1. Identify what the file claims to be based on its extension
    _, ext = os.path.splitext(file_path)
    normalized_ext = ext.lower()

    if normalized_ext not in MAGIC_NUMBERS:
        raise ValueError(f"Quarantine protocol rejected unrecognized format type: {ext}")

    expected_signatures = MAGIC_NUMBERS[normalized_ext]
    
    # Track the largest byte size we need to pull to evaluate the file properly
    max_read_bytes = max(len(sig) for sig in expected_signatures)

    # 2. Extract the raw binary bytes from the front of the file
    try:
        with open(file_path, 'rb') as f:
            file_header = f.read(max_read_bytes)
    except Exception as e:
        raise ValueError(f"Failed to initialize binary stream checkpoint: {str(e)}")

    # 3. Match the file header against our verified signature profiles
    is_verified = False
    for signature in expected_signatures:
        # Match data slicing exactly to the length of the specific format signature variation
        if file_header.startswith(signature[:len(signature)]):
            is_verified = True
            break

    if not is_verified:
        raise ValueError(
            f"Security Alert: Content spoof detected! The file extension claims to be '{ext}', "
            f"but its internal binary signature does not match an authentic {ext.upper()} document configuration."
        )

    return True
    
