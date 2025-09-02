import sys
import os
import urllib.request
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dotenv import load_dotenv

def check_node_status(port):
    """Check if a Weaviate node is healthy"""
    try:
        url = f"http://localhost:{port}/v1/meta"
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return {
                    'port': port,
                    'hostname': data.get('hostname', 'unknown'),
                    'version': data.get('version', 'unknown'),
                    'healthy': True
                }
            else:
                return {
                    'port': port,
                    'error': f'HTTP {response.status}',
                    'healthy': False
                }
    except Exception as e:
        return {
            'port': port,
            'error': str(e),
            'healthy': False
        }

def main():
    """Main function to check all 3 nodes"""
    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Get cluster ports from environment
    ports_str = os.environ.get("WEAVIATE_CLUSTER_PORTS", "18080,18081,18082")
    nodes = [int(port.strip()) for port in ports_str.split(",")]

    healthy_count = 0
    max_attempts = 10
    attempt = 0

    print("=== Weaviate Cluster Health Check ===")

    while attempt < max_attempts and healthy_count < len(nodes):
        attempt += 1
        print(f"\nAttempt {attempt}/{max_attempts}:")

        healthy_count = 0
        for port in nodes:
            status = check_node_status(port)
            if status['healthy']:
                print(f"✅ Node {port}: Healthy")
                print(f"   Hostname: {status['hostname']}")
                print(f"   Version: {status['version']}")
                healthy_count += 1
            else:
                print(f"❌ Node {port}: Unhealthy")
                if 'error' in status:
                    print(f"   Error: {status['error']}")

        if healthy_count < len(nodes):
            print(f"Waiting... ({healthy_count}/{len(nodes)} nodes healthy)")
            time.sleep(10)

    print(f"\nFinal Summary: {healthy_count}/{len(nodes)} nodes healthy")

    if healthy_count == len(nodes):
        print("🎉 All nodes are healthy!")
        return True
    else:
        print("⚠️  Some nodes are still unhealthy")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)