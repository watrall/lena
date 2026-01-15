#!/usr/bin/env python3
"""Quick sanity check to verify the /courses endpoint is responding.

Run this script after starting the backend to confirm the API is accessible.
"""

import urllib.error
import urllib.request

try:
    with urllib.request.urlopen("http://localhost:8000/courses", timeout=5) as response:
        print(f"Status Code: {response.getcode()}")
        print(f"Response: {response.read().decode('utf-8')}")
except urllib.error.URLError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Error: {e}")
