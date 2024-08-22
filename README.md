# Test Crossref DOIs

Script to test retrieving data from the Crossref API and resolving DOIs.


## Usage
```
pip install -r requirements.txt
```

## Usage

```
python script.py -i input.csv -o output.csv [OPTIONS]
```

### Required Arguments

- `-i, --input`: Path to input CSV file
- `-o, --output`: Path to output CSV file

### Optional Arguments

- `-k, --apikey`: Crossref API key (Metadata Plus Access)
- `-u, --user_agent`: User Agent string (use mailto:email@address.xyz)
- `-s, --sample_size`: Number of DOIs to sample
- `--retrieve`: Retrieve data from Crossref API
- `--resolve`: Resolve DOIs
- `--sleep`: Sleep interval between requests (default: 1.0s)

## Input Format

CSV file with a 'doi' column.

## Output

CSV file with original DOI, API response (if retrieved), resolved URL (if resolved), and resulting status.