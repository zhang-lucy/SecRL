# -*- coding: utf-8 -*-
"""
Croissant file generator for data in test folder
"""

import mlcroissant as mlc
import json
import os
import glob
from pathlib import Path

# Define the path to your test folder
TEST_FOLDER = "/Users/kevin/Downloads/SecRL/secgym/env/questions/min_overlap/test"  # Update this path as needed
OUTPUT_FILE = "/Users/kevin/Downloads/SecRL/notebooks/croissant.json"  # Output file for the Croissant JSON-LD

# Function to scan and analyze the test folder
def scan_test_folder(folder_path):
    print(f"Scanning folder: {folder_path}")
    
    # List all files in the directory
    files = []
    for ext in ["*.*"]:  # Add specific extensions if needed
        pattern = os.path.join(folder_path, ext)
        files.extend(glob.glob(pattern))
    
    print(f"Found {len(files)} files")
    for f in files:
        print(f" - {os.path.basename(f)}")
    
    return files

# Scan the test folder
test_files = scan_test_folder(TEST_FOLDER)

# Create FileObjects and FileSets
distribution = [
    # Main folder as a FileObject
    mlc.FileObject(
        id="test-folder",
        name="test-folder",
        description="Test data folder containing dataset files.",
        content_url=TEST_FOLDER,
        encoding_formats=["directory"],
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # Adding a placeholder SHA256
    )
]

# Add individual files or file groups
# For example, if you have CSV files:
csv_files = [f for f in test_files if f.endswith('.csv')]
if csv_files:
    distribution.append(
        mlc.FileSet(
            id="csv-files",
            name="csv-files",
            description="CSV files in the test folder.",
            contained_in=["test-folder"],
            encoding_formats=["text/csv"],
            includes="*.csv",
        )
    )

# For JSON files - with more specific handling for incident files
json_files = [f for f in test_files if f.endswith('.json')]
if json_files:
    distribution.append(
        mlc.FileSet(
            id="json-files",
            name="json-files",
            description="Security incident JSON files in the test folder.",
            contained_in=["test-folder"],
            encoding_formats=["application/json"],
            includes="incident_*.json",
        )
    )

# For text files
txt_files = [f for f in test_files if f.endswith('.txt')]
if txt_files:
    distribution.append(
        mlc.FileSet(
            id="text-files",
            name="text-files",
            description="Text files in the test folder.",
            contained_in=["test-folder"],
            encoding_formats=["text/plain"],
            includes="*.txt",
        )
    )

# Add more file types as needed based on your test folder content

# Define RecordSets
record_sets = []

# Example for CSV files (adjust fields based on your CSV structure)
if csv_files:
    # Try to detect columns from the first CSV file
    csv_fields = []
    try:
        import pandas as pd
        sample_csv = csv_files[0]
        df = pd.read_csv(sample_csv, nrows=1)
        
        for column in df.columns:
            csv_fields.append(
                mlc.Field(
                    id=f"csv/{column}",
                    name=column,
                    description=f"Column {column} from CSV files",
                    data_types=mlc.DataType.TEXT,  # Adjust type as needed
                    source=mlc.Source(
                        file_set="csv-files",
                        extract=mlc.Extract(column=column),
                    ),
                )
            )
    except Exception as e:
        print(f"Could not analyze CSV file: {e}")
        # Fallback to a generic field
        csv_fields = [
            mlc.Field(
                id="csv/content",
                name="content",
                description="Content from CSV files",
                data_types=mlc.DataType.TEXT,
                source=mlc.Source(
                    file_set="csv-files",
                    extract=mlc.Extract(column="*"),  # Generic extraction
                ),
            )
        ]
    
    record_sets.append(
        mlc.RecordSet(
            id="csv",
            name="csv",
            fields=csv_fields,
        )
    )

# Specialized RecordSet for JSON files with incident data
if json_files:
    record_sets.append(
        mlc.RecordSet(
            id="incidents",
            name="security_incidents",
            fields=[
                mlc.Field(
                    id="incident/id",
                    name="incident_id",
                    description="Incident identifier extracted from filename",
                    data_types=mlc.DataType.TEXT,
                    source=mlc.Source(
                        file_set="json-files",
                        extract=mlc.Extract(
                            file_property=mlc._src.structure_graph.nodes.source.FileProperty.filename
                        ),
                        transforms=[mlc.Transform(regex="^incident_(\\d+)_.*\\.json$")],
                    ),
                ),
                mlc.Field(
                    id="incident/content",
                    name="content",
                    description="Content from security incident JSON files",
                    data_types=mlc.DataType.TEXT,
                    source=mlc.Source(
                        file_set="json-files",
                        extract=mlc.Extract(column="*"),
                    ),
                )
            ],
        )
    )

# Example for text files
if txt_files:
    record_sets.append(
        mlc.RecordSet(
            id="text",
            name="text",
            fields=[
                mlc.Field(
                    id="text/content",
                    name="content",
                    description="Content from text files",
                    data_types=mlc.DataType.TEXT,
                    source=mlc.Source(
                        file_set="text-files",
                        extract=mlc.Extract(text="*"),  # Extract all text
                    ),
                )
            ],
        )
    )

# Create metadata with more detailed description
metadata = mlc.Metadata(
    name="Security Incident Dataset",
    description="Collection of security incident data in JSON format for security question-answer analysis.",
    url=f"file://{TEST_FOLDER}",
    distribution=distribution,
    record_sets=record_sets,
    license="https://creativecommons.org/licenses/by/4.0/",
)

# Print issues
print(metadata.issues.report())

# Write the Croissant JSON-LD to a file
with open(OUTPUT_FILE, "w") as f:
    content = metadata.to_json()
    content = json.dumps(content, indent=2)
    f.write(content)
    f.write("\n")  # Terminate file with newline

print(f"Croissant file written to: {OUTPUT_FILE}")

# Optional: Load and validate the created dataset
try:
    dataset = mlc.Dataset(jsonld=OUTPUT_FILE)
    print("Dataset validated successfully")
    
    # Try to load records from the first record set
    if record_sets:
        first_record_set = record_sets[0].id
        print(f"Sample records from '{first_record_set}':")
        records = dataset.records(record_set=first_record_set)
        
        for i, record in enumerate(records):
            print(record)
            if i >= 3:  # Show only first few records
                break
except Exception as e:
    print(f"Error validating dataset: {e}")

