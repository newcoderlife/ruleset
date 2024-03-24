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
    parser.add_argument('--result', metavar='RESULT', type=str, help='Path to the existing non-China domain ruleset or new ruleset', default='ruleset.noncn')
    parser.add_argument('--exception', metavar='EXCEPTION', type=str, help='Path to the exception ruleset', default='ruleset.cn')
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

            try:
                if reader.country(ip).country.iso_code == 'CN':
                    continue
            except geoip2.errors.AddressNotFoundError:
                print('Address not found:', domain, ip)
                continue

            result.append(domain)
    reader.close()
    
    try:
        with open(args.result, 'r') as f:
            result.extend(f.readlines())
    except FileNotFoundError:
        print('No existing ruleset found, creating new ruleset...')

    exception = []
    try:
        with open(args.exception, 'r') as f:
            exception.extend(f.readlines())
            exception = [domain.strip() for domain in exception if len(domain.strip()) > 0]
    except FileNotFoundError:
        print('No exception ruleset found, skipping...')

    dedup = {}
    result = [domain.strip() for domain in result if len(domain.strip()) > 0]
    for subdomain in result:
        dedup[subdomain] = True

        for domain in exception:
            if subdomain.endswith(domain):
                dedup[subdomain] = False
                break
        if not dedup[subdomain]:
            continue
        
        for domain in result:
            if subdomain.endswith(domain) and subdomain != domain:
                dedup[subdomain] = False
                break

    result = sorted([domain for domain in dedup if dedup[domain]])
    
    with open(args.result, 'w') as f:
        for domain in result:
            f.write(domain + '\n')