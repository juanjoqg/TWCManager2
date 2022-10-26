#!/usr/bin/env python3

import json
import requests

# Configuration
skipFailure = 0

# Disable environment import to avoid proxying requests
session = requests.Session()
session.trust_env = False

success = 1
response = None

try:
    response = session.get("http://127.0.0.1:8088/api/getLastTWCResponse", timeout=30)
except requests.Timeout:
    print("Error: Connection Timed Out")
    exit(255)
except requests.ConnectionError:
    print("Error: Connection Error")
    exit(255)

if response.status_code == 200:
    success = 1
else:
    print("Error: Response code " + str(response.status_code))
    exit(255)

if success:
    print("All tests successful")
    exit(0)
else:
    print("At least one test failed. Please review logs")
    if skipFailure:
        print("Due to skipFailure being set, we will not fail the test suite pipeline on this test.")
        exit(0)
    else:
        exit(255)
