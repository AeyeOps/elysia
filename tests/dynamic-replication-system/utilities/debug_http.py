#!/usr/bin/env python3

import http.client
import json

try:
    print("Testing HTTP connection...")
    conn = http.client.HTTPConnection("localhost", 18080, timeout=10)
    conn.request("GET", "/v1/meta")
    response = conn.getresponse()
    print(f"Status: {response.status}")
    if response.status == 200:
        data = json.loads(response.read().decode())
        print(f"Response: {data}")
    else:
        print(f"Response body: {response.read().decode()}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()