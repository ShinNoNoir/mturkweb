import os
import sys
import csv
import getpass
import StringIO
import argparse
import mturkweb

from collections import defaultdict

# Fix for CERTIFICATE_VERIFY_FAILED error in python 2.7.9 (see https://bugs.python.org/issue22417)
import ssl
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

CONSIDER_PAYMENT_TYPES = ['AssignmentPayment', 'BonusPayment']


def login_prompt():
    email = raw_input('Email: ')
    password = getpass.getpass('Password: ')
    return email, password

def parse_csv(csv_string):
    results = defaultdict(lambda: [0,0])
    csv_file = StringIO.StringIO(csv_string)
    csvreader = csv.DictReader(csv_file, delimiter=',')
    
    for row in csvreader:
        if row['Transaction Type'] in CONSIDER_PAYMENT_TYPES:
            sign = 1 if row['Amount'][0] != '-' else -1
            amount = float(row['Amount'].lstrip('-')) * sign
            results[row['Recipient ID']][0] += amount
            results[row['Recipient ID']][1] += 1
            
    csv_file.close()

    sorted_results = sorted([[k, v[0], v[1]] for k, v in results.iteritems()], key=lambda x: x[1])
    return sorted_results

def main(argv):
    parser = argparse.ArgumentParser(description='Download the transaction history from mturk')

    parser.add_argument('year', help='The year you want the transaction history for')
    parser.add_argument('--amount', help='Only print payments above this threshold (in $, default: 10)', default=10)
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(2)
            
    try:
        args = parser.parse_args(sys.argv[1:])
    except argparse.ArgumentError:
        parser.print_help()
        sys.exit(2)
    
    try:
        email, password = login_prompt()
        session = mturkweb.login(email, password)
        transactions = session.get_transaction_history_csv(int(args.year))
    except Exception, e:
        print 'Error:', str(e)
        sys.exit(1) 

    sorted_results = parse_csv(transactions)
    amount_threshold = float(args.amount) * -1
    print '\n%-20s%10s%10s\n' % ('Worker', 'Amount', '#HITS')
    for worker, amount, times in sorted_results:
        if amount < amount_threshold:
            print '%-20s%10.2f%10s' % (worker, amount, times)
    
if __name__ == "__main__":
    main(sys.argv[1:])
