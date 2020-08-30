#!/usr/bin/python

import argparse
import json
import re
import six
import sys
import xrdinfo

DEFAULT_TIMEOUT = 5.0
REPORT_FILE = 'riha_4_reports.json'
STATUS_PRIORITY = {
    'IN_USE': 1,
    'ESTABLISHING': 2,
    'FINISHED': 3,
    'NULL': 9,
}


def print_error(content):
    """Thread safe and unicode safe error printer."""
    content = u"ERROR: {}\n".format(content)
    if six.PY2:
        sys.stderr.write(content.encode('utf-8'))
    else:
        sys.stderr.write(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='List Subsystems info based on RIHA and X-Road global configuration.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='You need to provide either Security Server or Central Server address.\n\n'
               'NB! Global configuration signature is not validated when using Central Server.\n'
               'Use local Security Server whenever possible.'
    )
    parser.add_argument(
        '-s', metavar='SECURITY_SERVER', help='DNS name/IP/URL of local Security Server')
    parser.add_argument(
        '-c', metavar='CENTRAL_SERVER',
        help='DNS name/IP/URL of Central Server/Configuration Proxy')
    parser.add_argument('-t', metavar='TIMEOUT', help='timeout for HTTP query', type=float)
    parser.add_argument('--riha', metavar='RIHA_JSON', help='RIHA data file in json format.')
    args = parser.parse_args()

    timeout = DEFAULT_TIMEOUT
    if args.t:
        timeout = args.t

    sharedParams = None
    if args.s:
        try:
            sharedParams = xrdinfo.shared_params_ss(addr=args.s, timeout=timeout)
        except xrdinfo.XrdInfoError as e:
            print_error(e)
            exit(1)
    elif args.c:
        try:
            sharedParams = xrdinfo.shared_params_cs(addr=args.c, timeout=timeout)
        except xrdinfo.XrdInfoError as e:
            print_error(e)
            exit(1)
    else:
        parser.print_help()
        exit(1)

    if six.PY2:
        # Convert to unicode
        args.riha = args.riha.decode('utf-8')

    jsonData = None
    if args.riha:
        try:
            if six.PY2:
                with open(args.riha, 'r') as f:
                    jsonData = json.loads(f.read().decode('utf-8'))
            else:
                with open(args.riha, 'r', encoding="utf-8") as f:
                    jsonData = json.load(f)
        except Exception as e:
            print_error('Cannot load file {}; error: {}'.format(args.riha, e))

    rihaSystems = {}
    if jsonData:
        for item in jsonData['content']:
            systemCode = ''
            systemName = ''
            ownerCode = ''
            ownerName = ''
            contacts = []
            if 'details' in item:
                if 'short_name' in item['details']:
                    systemCode = item['details']['short_name']
                if 'name' in item['details']:
                    systemName = item['details']['name']
                if 'owner' in item['details']:
                    if 'code' in item['details']['owner']:
                        ownerCode = item['details']['owner']['code']
                    if 'name' in item['details']['owner']:
                        ownerName = item['details']['owner']['name']
                if 'contacts' in item['details'] and item['details']['contacts'] is not None:
                    for contact in item['details']['contacts']:
                        email = ''
                        name = ''
                        if 'email' in contact:
                            email = contact['email']
                        if 'name' in contact:
                            name = contact['name']
                        contacts.append({'email': email, 'name': name})

            systemStatus = None
            try:
                systemStatus = item['details']['meta']['system_status']['status']
            except KeyError:
                # print("KeyError for ", ownerCode, "/", systemCode, "(", systemName, ownerName, ")") 
                pass
            if not systemStatus:
                # Default status is "NULL"
                systemStatus = 'NULL'
                # print("Default status ", systemStatus, " set for ", ownerCode, "/", systemCode, "(", systemName, ownerName, ")") 

            val = {'systemName': systemName, 'ownerName': ownerName, 'contacts': contacts,
                   'status': systemStatus}
            # The .lower() here and later should be considered as
            # a temporary hack to find matching data in RIHA
            # and in X-Road global configuration.
            # Instead of that there should be a proper one to one
            # relation between RIHA and X-Road global configuration.
            id1 = '{}/{}'.format(ownerCode, systemCode.lower())
            # Replacing value only if its status has higher priority
            if (id1 not in rihaSystems or STATUS_PRIORITY[systemStatus] <= STATUS_PRIORITY[
                    rihaSystems[id1]['status']]):
                rihaSystems[id1] = val
                # print(id1, rihaSystems[id1])
            # else: print("System id1 ", ownerCode, "/", systemCode, " exists already with status ", systemStatus, "(", systemName, ownerName, ")")

            # The matches of RIHA "memberCode/memberCode-subSystemCode"
            # and/or "another_memberCode/memberCode-subSystemCode"
            # should considered as a temporary hack
            m = re.match("^(\d{8})-(.+)$", systemCode)
            if m:
                # RIHA "memberCode/memberCode-subSystemCode" subsystem
                # might be X-Road "memberCode/subSystemCode" subsystem
                id2 = '{}/{}'.format(ownerCode, m.group(2).lower())
                # Replacing value only if its status has higher priority
                if (id2 not in rihaSystems or STATUS_PRIORITY[systemStatus] <= STATUS_PRIORITY[
                        rihaSystems[id2]['status']]):
                    rihaSystems[id2] = val
                    # print(id2, rihaSystems[id2])
                # else: print("System id2 ", ownerCode, "/", systemCode, " exists already with status ", systemStatus, "(", systemName, ownerName, ")")

                # RIHA "another_memberCode/memberCode-subSystemCode"
                # might be X-Road "memberCode/subSystemCode"
                id3 = '{}/{}'.format(m.group(1), m.group(2).lower())
                # Replacing value only if its status has higher priority
                if (id3 not in rihaSystems or STATUS_PRIORITY[systemStatus] <= STATUS_PRIORITY[
                        rihaSystems[id3]['status']]):
                    rihaSystems[id3] = val
                    # print(id3, rihaSystems[id3])
                # else: print("System id3 ", ownerCode, "/", systemCode, " exists already with status ", systemStatus, "(", systemName, ownerName, ")")

            # Fix for RIHA NEE
            # RIHA short_name "NTR??-*-subSystemCode" might be X-Road
            # "NTR??-*/subSystemCode"
            m = re.match("^NTR(.{2})-(.+)-(.+)$", systemCode)
            if m:
                id4 = 'NTR{}-{}/{}'.format(m.group(1), m.group(2), m.group(3).lower())
                # Replacing value only if its status has higher priority
                if (id4 not in rihaSystems or STATUS_PRIORITY[systemStatus] <= STATUS_PRIORITY[
                        rihaSystems[id4]['status']]):
                    rihaSystems[id4] = val
                    # print(id4, rihaSystems[id4])
                # else: print("System id4 ", ownerCode, "/", systemCode, " exists already with status ", systemStatus, "(", systemName, ownerName, ")")

    registered = None
    try:
        registered = list(xrdinfo.registered_subsystems(sharedParams))
    except xrdinfo.XrdInfoError as e:
        print_error(e)
        exit(1)

    jsonDataArr = []
    try:
        for subsystem in xrdinfo.subsystems_with_membername(sharedParams):
            # Example: ('ee-dev', 'GOV', '70006317', 'testservice',
            # u'Riigi Infos\xfcsteemi Amet')

            if subsystem[0:4] not in registered:
                # print('Not registered: {}'.format(subsystem))
                continue

            # The .lower() here and before should be considered as
            # a temporary hack to find matching data in RIHA
            # and in X-Road global configuration.
            id = '{}/{}'.format(subsystem[2], subsystem[3].lower())
            if id in rihaSystems:
                jsonData = {
                    'x_road_instance': subsystem[0],
                    'member_class': subsystem[1],
                    'member_code': subsystem[2],
                    'member_name': rihaSystems[id]['ownerName'] if rihaSystems[id][
                        'ownerName'] else subsystem[4],
                    'subsystem_code': subsystem[3],
                    'subsystem_name': {'et': rihaSystems[id]['systemName'], 'en': ''},
                    'email': rihaSystems[id]['contacts']
                }
            else:
                jsonData = {
                    'x_road_instance': subsystem[0],
                    'member_class': subsystem[1],
                    'member_code': subsystem[2],
                    'member_name': subsystem[4],
                    'subsystem_code': subsystem[3],
                    'subsystem_name': {'et': '', 'en': ''},
                    'email': []
                }
            # print(json.dumps(jsonData, indent=2, ensure_ascii=False))
            jsonDataArr.append(jsonData)
    except xrdinfo.XrdInfoError as e:
        print_error(e)
        exit(1)

    if six.PY2:
        with open(REPORT_FILE, 'w') as f:
            f.write(json.dumps(
                jsonDataArr, indent=2, ensure_ascii=False, sort_keys=True).encode('utf-8'))
    else:
        with open(REPORT_FILE, 'w', encoding="utf-8") as f:
            json.dump(jsonDataArr, f, indent=2, ensure_ascii=False, sort_keys=True)
