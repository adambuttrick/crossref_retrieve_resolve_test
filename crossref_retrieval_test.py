import argparse
import csv
import random
import requests
import time
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Retrieve data from Crossref API or resolve DOIs')
    parser.add_argument('-i', '--input', required=True,
                        help='Path to input CSV file')
    parser.add_argument('-o', '--output', required=True,
                        help='Path to output CSV file')
    parser.add_argument('-k', '--apikey', required=False,
                        help='Crossref API key (optional)')
    parser.add_argument('-u', '--user_agent', required=False,
                        help='User Agent string (optional)')
    parser.add_argument('-s', '--sample_size', type=int, required=False,
                        help='Number of samples to retrieve (optional)')
    parser.add_argument('--retrieve', action='store_true',
                        help='Retrieve data from Crossref API')
    parser.add_argument('--resolve', action='store_true',
                        help='Resolve DOIs')
    parser.add_argument('--sleep', type=float, default=1.0,
                        help='Sleep interval between requests in seconds (default: 1.0, disabled if API key is provided)')
    args = parser.parse_args()
    if not (args.retrieve or args.resolve):
        parser.error(
            "At least one of --retrieve or --resolve must be specified.")
    return args


def read_csv(input_file):
    with open(input_file, 'r') as file:
        reader = csv.DictReader(file)
        return list(reader)


def sample_dois(data, sample_size):
    return random.sample(data, sample_size) if sample_size and sample_size < len(data) else data


def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.1)
    session.mount('https://', HTTPAdapter(max_retries=retry))
    return session


def crossref_request(doi, apikey, user_agent, session):
    url = f"https://api.crossref.org/works/{doi}"
    headers = {}
    if apikey:
        headers['Crossref-Plus-API-Token'] = f'Bearer {apikey}'
    if user_agent:
        headers['User-Agent'] = user_agent
    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request for DOI {doi} failed: {e}")
        return None


def resolve_doi(doi, session):
    try:
        response = session.head(f"https://doi.org/{doi}", allow_redirects=True)
        return response.url if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to resolve DOI {doi}: {e}")
        return None


def write_header(output_file, retrieve, resolve):
    with open(output_file, mode='w') as file:
        writer = csv.writer(file)
        header = ['doi']
        if retrieve:
            header.append('API_Response')
        if resolve:
            header.append('Resolved_URL')
        header.append('Status')
        writer.writerow(header)


def log_to_csv(output_file, data):
    with open(output_file, mode='a') as file:
        writer = csv.writer(file)
        writer.writerow(data)


def main():
    args = parse_args()
    data = read_csv(args.input)
    processed_data = sample_dois(data, args.sample_size)
    write_header(args.output, args.retrieve, args.resolve)
    session = get_session()
    use_sleep = not args.apikey and args.sleep > 0
    for row in processed_data:
        doi = row.get('doi')
        if not doi:
            logging.warning("Row without DOI found, skipping")
            continue
        logging.info(f"Processing DOI: {doi}")
        output_row = [doi]
        status = "Success"
        if args.retrieve:
            api_response = crossref_request(
                doi, args.apikey, args.user_agent, session)
            if api_response:
                output_row.append(api_response)
                logging.info(f"Successfully retrieved data for DOI: {doi}")
            else:
                output_row.append("No data available")
                status = "Failure"
                logging.warning(f"Failed to retrieve data for DOI: {doi}")
        if args.resolve:
            resolved_url = resolve_doi(doi, session)
            if resolved_url:
                output_row.append(resolved_url)
                logging.info(f"Successfully resolved DOI: {doi}")
            else:
                output_row.append("Resolution failed")
                status = "Failure"
                logging.warning(f"Failed to resolve DOI: {doi}")
        output_row.append(status)
        log_to_csv(args.output, output_row)
        if use_sleep:
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
