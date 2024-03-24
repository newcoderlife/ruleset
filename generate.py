#!/usr/bin/env python3

import argparse
import re
import geoip2.database

pattern = r'\[INFO\] A ((?:(?:[a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)+[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?\.) \b(?:\d{1,3}\.){3}\d{1,3}:\d+\b \d+.\d+s (\b(?:\d{1,3}\.){3}\d{1,3}\b)'

def parse_args():
    parser = argparse.ArgumentParser(description='Generate non-China domain ruleset for pforward')
    parser.add_argument('--geo_database', metavar='GEO_DATABASE', type=str, help='Path to the GeoLite2-Country.mmdb database', default='GeoLite2-Country.mmdb')
    parser.add_argument('--log_file', metavar='LOG_FILE', type=str, help='Path to coredns log file')
    parser.add_argument('--log_format', metavar='LOG_FORMAT', type=str, help='Regex format for coredns log file', default=pattern)
    parser.add_argument('--result', metavar='RESULT', type=str, help='Path to the existing non-China domain ruleset or new ruleset', default='ruleset.txt')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    regex = re.compile(args.log_format)
    result = []
    reader = geoip2.database.Reader(args.geo_database)
    with open(args.log_file, 'r') as f:
        for line in f:
            match = regex.match(line)
            if match is None or len(match.groups()) != 2:
                continue

            domain = match.group(1).strip()
            ip = match.group(2).strip()
            if len(domain) == 0 or len(ip) == 0:
                continue

            if reader.country(ip).country.iso_code == 'CN':
                continue

            result.append(domain)
    reader.close()
    
    try:
        with open(args.result, 'r') as f:
            result.extend(f.readlines())
            result = list(set(result))
    except FileNotFoundError:
        print('No existing ruleset found, creating new ruleset...')
    
    with open(args.result, 'w') as f:
        for domain in result:
            domain = domain.strip()
            if len(domain) == 0:
                continue
            f.write(domain + '\n')