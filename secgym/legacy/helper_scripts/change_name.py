import os

def rename_metadata_files(directory):
    # Iterate over all files in the specified directory
    for filename in os.listdir(directory):
        # Check if the file ends with "_metadata.json"
        if filename.endswith("_metadata.json"):
            # Create the new filename by replacing "_metadata.json" with ".meta"
            new_filename = filename.replace("_metadata.json", ".meta")
            # Get the full file paths
            old_file_path = os.path.join(directory, filename)
            new_file_path = os.path.join(directory, new_filename)
            # Rename the file
            os.rename(old_file_path, new_file_path)
            print(f"Renamed: {old_file_path} -> {new_file_path}")

# Example usage
# rename_metadata_files("/path/to/your/directory")


rename_metadata_files("./data/incidents/incident_322")