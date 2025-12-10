def validate_directory(dir_path: str, expected_id: str) -> bool:
    """Ensure directory .id file matches expected ULID."""
    id_file = os.path.join(dir_path, ".id")
    if not os.path.exists(id_file):
        return False
    with open(id_file) as f:
        return f.read().strip() == expected_id
