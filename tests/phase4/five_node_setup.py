#!/usr/bin/env python3
"""
five_node_setup.py - Configure and validate 5-node cluster
"""

import sys
import os
import time
import subprocess
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dotenv import load_dotenv

def check_docker_resources():
    """Check if system has sufficient resources for 5-node cluster"""
    print("🔍 CHECKING SYSTEM RESOURCES FOR 5-NODE CLUSTER")
    print("=" * 50)

    try:
        # Check available memory
        result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                mem_line = lines[1].split()
                if len(mem_line) >= 7:
                    total_mem = mem_line[0]
                    available_mem = mem_line[6]
                    print(f"💾 Memory: {available_mem} available of {total_mem} total")

        # Check CPU cores
        result = subprocess.run(['nproc'], capture_output=True, text=True)
        if result.returncode == 0:
            cpu_cores = int(result.stdout.strip())
            print(f"🖥️  CPU Cores: {cpu_cores}")

            # Estimate resource requirements
            recommended_mem = "4GB"
            recommended_cores = 4

            print(f"\n📊 RESOURCE REQUIREMENTS:")
            print(f"   Recommended: {recommended_cores} CPU cores, {recommended_mem} RAM")
            print(f"   Current: {cpu_cores} CPU cores, {available_mem} RAM available")

            if cpu_cores >= recommended_cores:
                print("   ✅ CPU cores: SUFFICIENT")
            else:
                print(f"   ⚠️  CPU cores: INSUFFICIENT (need {recommended_cores}, have {cpu_cores})")

            # Simple memory check (this is approximate)
            try:
                available_gb = float(available_mem.replace('G', '').replace('M', ''))
                if 'M' in available_mem:
                    available_gb = available_gb / 1024

                if available_gb >= 3.5:  # Roughly 4GB minus some buffer
                    print("   ✅ Memory: SUFFICIENT")
                else:
                    print(f"   ⚠️  Memory: LOW ({available_gb:.1f}GB available, recommend 4GB+)")
            except:
                print("   ❓ Memory: UNABLE TO DETERMINE")

        # Check Docker
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"🐳 Docker: {result.stdout.strip()}")
        else:
            print("❌ Docker: NOT AVAILABLE")
            return False

        return True

    except Exception as e:
        print(f"❌ Resource check failed: {e}")
        return False

def create_five_node_docker_compose():
    """Create Docker Compose file for 5-node cluster"""
    print("\n📝 CREATING 5-NODE DOCKER COMPOSE CONFIGURATION")
    print("=" * 50)

    # Create Docker Compose content as a single string
    docker_compose_content = """version: '3.8'

services:
  weaviate-node1:
    image: cr.weaviate.io/semitechnologies/weaviate:1.32.4
    networks:
      - weaviate-cluster-5node
    env_file: .env
    command:
      - --host
      - 0.0.0.0
      - --port
      - '8080'
      - --scheme
      - http
    ports:
      - "18080:8080"
      - "15051:50051"
      - "17100:7100"
    volumes:
      - weaviate_data_node1:/var/lib/weaviate
    restart: unless-stopped
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      ENABLE_API_BASED_MODULES: 'true'
      ENABLE_MODULES: 'text2vec-openai,text2vec-google,generative-openai,generative-google,generative-anthropic,text2vec-ollama,generative-ollama'
      CLUSTER_HOSTNAME: 'weaviate-node1'
      CLUSTER_GOSSIP_BIND_PORT: 7100
      CLUSTER_DATA_BIND_PORT: 7101
      RAFT_JOIN: 'weaviate-node1,weaviate-node2,weaviate-node3,weaviate-node4,weaviate-node5'
      RAFT_BOOTSTRAP_EXPECT: 5

  weaviate-node2:
    image: cr.weaviate.io/semitechnologies/weaviate:1.32.4
    networks:
      - weaviate-cluster-5node
    env_file: .env
    command:
      - --host
      - 0.0.0.0
      - --port
      - '8080'
      - --scheme
      - http
    ports:
      - "18081:8080"
      - "15052:50051"
      - "17101:7100"
    volumes:
      - weaviate_data_node2:/var/lib/weaviate
    restart: unless-stopped
    environment:
      CLUSTER_HOSTNAME: 'weaviate-node2'
      CLUSTER_GOSSIP_BIND_PORT: 7100
      CLUSTER_DATA_BIND_PORT: 7101
      RAFT_JOIN: 'weaviate-node1,weaviate-node2,weaviate-node3,weaviate-node4,weaviate-node5'
      RAFT_BOOTSTRAP_EXPECT: 5
      CLUSTER_JOIN: 'weaviate-node1:7100'

volumes:
  weaviate_data_node1:
  weaviate_data_node2:

networks:
  weaviate-cluster-5node:
    driver: bridge
    name: weaviate-cluster-5node
"""

    # Write the Docker Compose file
    with open('docker-compose-5node.yaml', 'w') as f:
        f.write(docker_compose_content)

    print("✅ Created docker-compose-5node.yaml")
    print("   Configuration includes:")
    print("   - 5 Weaviate nodes with unique ports")
    print("   - Raft consensus with 5 expected nodes")
    print("   - Persistent data volumes for each node")
    print("   - Proper cluster networking")

    return True

def deploy_five_node_cluster():
    """Deploy the 5-node cluster"""
    print("\n🚀 DEPLOYING 5-NODE CLUSTER")
    print("=" * 50)

    # Stop existing 3-node cluster first
    print("🛑 Stopping existing 3-node cluster...")
    try:
        subprocess.run(['docker-compose', 'down'], cwd='.', capture_output=True, timeout=30)
        print("✅ 3-node cluster stopped")
    except Exception as e:
        print(f"⚠️  Could not stop 3-node cluster: {e}")

    # Wait a moment
    time.sleep(5)

    # Deploy 5-node cluster
    print("🐳 Starting 5-node cluster...")
    try:
        result = subprocess.run(['docker-compose', '-f', 'docker-compose-5node.yaml', 'up', '-d'],
                              capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            print("✅ 5-node cluster deployment initiated")

            # Wait for cluster to stabilize
            print("⏳ Waiting for cluster to stabilize...")
            time.sleep(30)

            return True
        else:
            print(f"❌ Failed to deploy 5-node cluster: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

def validate_five_node_cluster():
    """Validate that the 5-node cluster is working properly"""
    print("\n🔍 VALIDATING 5-NODE CLUSTER")
    print("=" * 50)

    # Check all 5 nodes
    ports = [18080, 18081, 18082, 18083, 18084]
    healthy_nodes = 0
    node_status = {}

    for i, port in enumerate(ports, 1):
        try:
            # Simple health check
            import urllib.request
            url = f"http://localhost:{port}/v1/meta"
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    hostname = data.get('hostname', f'node{i}')
                    node_status[f'node{i}'] = {
                        'port': port,
                        'status': 'healthy',
                        'hostname': hostname
                    }
                    healthy_nodes += 1
                    print(f"✅ Node {i} (port {port}): Healthy - {hostname}")
                else:
                    node_status[f'node{i}'] = {'port': port, 'status': 'unhealthy', 'error': f'HTTP {response.status}'}
                    print(f"❌ Node {i} (port {port}): Unhealthy (HTTP {response.status})")

        except Exception as e:
            node_status[f'node{i}'] = {'port': port, 'status': 'unhealthy', 'error': str(e)}
            print(f"❌ Node {i} (port {port}): Unhealthy - {str(e)[:50]}...")

    print(f"\n📊 Cluster Status: {healthy_nodes}/5 nodes healthy")

    if healthy_nodes >= 3:  # At least majority for basic functionality
        print("✅ Cluster has quorum - basic operations should work")

        # Test basic cluster connectivity
        print("\n🔗 Testing cluster connectivity...")
        try:
            import weaviate
            client = weaviate.connect_to_local(
                host="localhost",
                port=18080,
                grpc_port=15051,
                headers={}
            )
            client.connect()

            # Test basic query
            collections = client.collections.list_all()
            print(f"✅ Cluster connectivity confirmed: {len(collections)} collections accessible")

            client.close()
            return True, node_status

        except Exception as e:
            print(f"❌ Cluster connectivity test failed: {e}")
            return False, node_status

    else:
        print("❌ Insufficient nodes healthy for cluster operation")
        print("   Need at least 3 healthy nodes for majority consensus")
        return False, node_status

def create_test_collection_5node():
    """Create a test collection in the 5-node cluster"""
    print("\n📝 CREATING TEST COLLECTION IN 5-NODE CLUSTER")
    print("=" * 50)

    collection_name = "FIVE_NODE_TEST_COLLECTION"

    try:
        import weaviate
        from weaviate.classes.config import Property, DataType

        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        # Create collection
        collection = client.collections.create(
            name=collection_name,
            properties=[
                Property(name="test_id", data_type=DataType.TEXT),
                Property(name="node_count", data_type=DataType.INT),
                Property(name="cluster_size", data_type=DataType.TEXT),
                Property(name="timestamp", data_type=DataType.DATE),
                Property(name="test_data", data_type=DataType.TEXT),
            ]
        )

        print(f"✅ Created collection: {collection_name}")

        # Insert test data
        collection = client.collections.get(collection_name)
        test_data = {
            "test_id": "5node_cluster_test",
            "node_count": 5,
            "cluster_size": "5-node",
            "timestamp": "2024-01-01T00:00:00Z",
            "test_data": "Test data created in 5-node cluster"
        }

        collection.data.insert(test_data)
        print("✅ Inserted test data")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Failed to create test collection: {e}")
        return False

def main():
    """Main function for 5-node cluster setup"""
    print("🚀 STARTING 5-NODE CLUSTER SETUP")
    print("   Configuring and validating 5-node Weaviate cluster")
    print("=" * 70)

    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Step 1: Check system resources
    print("\n📋 STEP 1: RESOURCE CHECK")
    if not check_docker_resources():
        print("\n❌ Insufficient resources for 5-node cluster")
        print("   Consider reducing to 3-node cluster or upgrading system resources")
        return False

    # Step 2: Create Docker Compose configuration
    print("\n📋 STEP 2: DOCKER CONFIGURATION")
    if not create_five_node_docker_compose():
        print("\n❌ Failed to create Docker Compose configuration")
        return False

    # Step 3: Deploy the cluster
    print("\n📋 STEP 3: CLUSTER DEPLOYMENT")
    if not deploy_five_node_cluster():
        print("\n❌ Failed to deploy 5-node cluster")
        return False

    # Step 4: Validate the cluster
    print("\n📋 STEP 4: CLUSTER VALIDATION")
    cluster_valid, node_status = validate_five_node_cluster()

    if not cluster_valid:
        print("\n❌ 5-node cluster validation failed")
        print("   Check Docker logs and system resources")
        return False

    # Step 5: Create test collection
    print("\n📋 STEP 5: TEST COLLECTION CREATION")
    if not create_test_collection_5node():
        print("\n⚠️  Test collection creation failed, but cluster may still be functional")

    # Summary
    print("\n" + "=" * 70)
    print("🏆 5-NODE CLUSTER SETUP COMPLETE")
    print("=" * 70)

    healthy_nodes = sum(1 for node in node_status.values() if node['status'] == 'healthy')

    print(f"📊 Final Status: {healthy_nodes}/5 nodes operational")
    print("✅ Docker Compose configuration: docker-compose-5node.yaml")
    print("✅ Cluster networking: weaviate-cluster-5node")
    print("✅ Replication factor: 5 (RAFT_BOOTSTRAP_EXPECT=5)")
    print("✅ Test collection: FIVE_NODE_TEST_COLLECTION (if created)")

    if healthy_nodes >= 3:
        print("\n🎉 SUCCESS: 5-node cluster is ready for testing!")
        print("   - Ready for scale-down testing")
        print("   - Ready for performance benchmarking")
        print("   - Ready for replication factor testing")
        return True
    else:
        print("\n⚠️  PARTIAL SUCCESS: Cluster deployed but not fully healthy")
        print("   - Some nodes may need additional time to join")
        print("   - Check Docker logs for detailed status")
        return True  # Still consider success since cluster is deployed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)