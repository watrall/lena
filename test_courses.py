import urllib.request
import urllib.error
import sys

try:
    with urllib.request.urlopen("http://localhost:8000/courses", timeout=5) as response:
        print(f"Status Code: {response.getcode()}")
        print(f"Response: {response.read().decode('utf-8')}")
except urllib.error.URLError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Error: {e}")
