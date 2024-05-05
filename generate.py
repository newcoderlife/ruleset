#!/usr/bin/env python3

import argparse
import re
import os
import geoip2.database

pattern = r'\[INFO\] A ((?:(?:[a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)+[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?\.) \b(?:\d{1,3}\.){3}\d{1,3}:\d+\b( true| false| -)? \d+.\d+s (\b(?:\d{1,3}\.){3}\d{1,3}\b)'

def parse_args():
    parser = argparse.ArgumentParser(description='Generate non-China domain ruleset for pforward')
    parser.add_argument('--geo_database', metavar='GEO_DATABASE', type=str, help='Path to the GeoLite2-Country.mmdb database', default='Country.mmdb')
    parser.add_argument('--log_file', metavar='LOG_FILE', type=str, help='Path to coredns log file')
    parser.add_argument('--log_format', metavar='LOG_FORMAT', type=str, help='Regex format for coredns log file', default=pattern)
    return parser.parse_args()

def contains(subdomain: str, ruleset: list)->str:
    if ruleset is None:
        return ''
    
    result = ''
    for domain in ruleset:
        s = subdomain.split('.')[::-1]
        d = domain.split('.')[::-1]
        if len(d) > len(s):
            continue
        
        flag = True
        for i in range(len(d)):
            if d[i] != s[i]:
                flag = False
                break
        if flag and (result == '' or len(domain) < len(result)):
            result = domain
    return result

def read_ruleset(file_path: str)->list:
    dirname = os.path.dirname(file_path)

    result = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip() == '' or line.startswith('#'):
                    continue
                
                if line.startswith('include:'):
                    result.extend(read_ruleset(os.path.join(dirname, line.removeprefix('include:').strip())))
                else:
                    result.append(line.strip())
            print(f'read {file_path}')
    except FileNotFoundError:
        print(f'{file_path} not found')
    except Exception as e:
        print(f"read {file_path} except {e}")
    
    return result

if __name__ == '__main__':
    args = parse_args()

    noncn = read_ruleset('ruleset.noncn')
    cn = read_ruleset('cn')
    local = read_ruleset('local.noncn')

    regex = re.compile(args.log_format)
    reader = geoip2.database.Reader(args.geo_database)
    with open(args.log_file, 'r') as f:
        for line in f:
            match = regex.match(line)
            if match is None or len(match.groups()) < 2:
                continue

            domain = match.group(1).strip()
            ip = match.group(3).strip()
            if len(domain) == 0 or len(ip) == 0:
                continue

            try:
                if reader.country(ip).country.iso_code == 'CN':
                    continue
            except geoip2.errors.AddressNotFoundError:
                print('Address not found:', domain, ip)
                continue

            local.append(domain)
    reader.close()

    local = sorted(list(set(local)))
    local = [domain for domain in local if contains(domain, local) == domain and contains(domain, noncn) == '' and contains(domain, cn) == '' and domain != '']
    
    with open('local.noncn', 'w') as f:
        f.write('# Put your domain here. Format like `twitter.com.`.\n')
        for domain in local:
            f.write(domain + '\n')
