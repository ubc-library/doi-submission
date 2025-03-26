# UBC Library DOI Script

This script submits Digital Object Identifiers (DOIs) and their associated metadata to DataCite.

## Getting Started

Copy `config/config.ini.example` to `config/config.ini` and fill out the environment variables.

## Usage
```
python3 update_minted_public.py
```

## Files

- updated_minted_public.py - Script for DOI submission
- config/config.ini - Contains environment variables required to run the DOI submission script
- example_files/items.json - List of example items
  - item_info_*.json - Example item metadata used to map to DataCite metadata
  - {:doi}.txt - (Example TXT file generated for submission to DataCite /doi endpoint)
  - {:doi}.xml - (Example XML metadata generated for submission to DataCite /metadata endpoint, reformatted for clarity)
- FAILED_DOI - Folder for holding failed submissions
