#!/usr/bin/env python3
"""
simple_check.py - Simple health check for Weaviate nodes
"""

import socket
import time
import urllib.request

def check_port(port):
    """Check if port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except:
        return False

def check_weaviate_health(port):
    """Check if Weaviate node is responding"""
    try:
        url = f"http://localhost:{port}/v1/meta"
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except:
        return False

def main():
    nodes = [18080, 18081, 18082]
    port_healthy_count = 0
    weaviate_healthy_count = 0

    print("=== Weaviate Cluster Health Check ===")

    for port in nodes:
        port_open = check_port(port)
        weaviate_healthy = check_weaviate_health(port)

        if port_open:
            print(f"✅ Port {port}: Open")
            port_healthy_count += 1
        else:
            print(f"❌ Port {port}: Closed")

        if weaviate_healthy:
            print(f"✅ Weaviate {port}: Healthy")
            weaviate_healthy_count += 1
        else:
            print(f"❌ Weaviate {port}: Unhealthy")

    print(f"\nSummary:")
    print(f"  Ports: {port_healthy_count}/3 open")
    print(f"  Weaviate: {weaviate_healthy_count}/3 healthy")

    if port_healthy_count == 3 and weaviate_healthy_count == 3:
        print("🎉 Cluster is fully healthy!")
        return True
    elif port_healthy_count >= 2 and weaviate_healthy_count >= 2:
        print("⚠️  Cluster is partially healthy (may work for testing)")
        return True
    else:
        print("❌ Cluster health issues detected")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)