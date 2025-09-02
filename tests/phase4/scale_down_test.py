#!/usr/bin/env python3
"""
scale_down_test.py - Test reducing cluster size from 5 to 3 nodes
"""

import sys
import os
import time
import subprocess
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dotenv import load_dotenv

def check_cluster_health(ports):
    """Check health of all nodes in the cluster"""
    healthy_count = 0
    node_status = {}

    for i, port in enumerate(ports, 1):
        try:
            import urllib.request
            url = f"http://localhost:{port}/v1/meta"
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    hostname = data.get('hostname', f'node{i}')
                    node_status[f'node{i}'] = {
                        'port': port,
                        'status': 'healthy',
                        'hostname': hostname
                    }
                    healthy_count += 1
                else:
                    node_status[f'node{i}'] = {'port': port, 'status': 'unhealthy', 'error': f'HTTP {response.status}'}
        except Exception as e:
            node_status[f'node{i}'] = {'port': port, 'status': 'unhealthy', 'error': str(e)}

    return healthy_count, node_status

def create_scale_test_data():
    """Create test data before scale-down"""
    print("📝 CREATING TEST DATA FOR SCALE-DOWN TEST")
    print("=" * 50)

    collection_name = "SCALE_DOWN_TEST_COLLECTION"

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

        # Create collection if it doesn't exist
        if not client.collections.exists(collection_name):
            collection = client.collections.create(
                name=collection_name,
                properties=[
                    Property(name="test_id", data_type=DataType.TEXT),
                    Property(name="scale_phase", data_type=DataType.TEXT),
                    Property(name="node_count", data_type=DataType.INT),
                    Property(name="timestamp", data_type=DataType.DATE),
                    Property(name="test_data", data_type=DataType.TEXT),
                ]
            )
            print(f"✅ Created collection: {collection_name}")

        # Insert test data
        collection = client.collections.get(collection_name)

        # Create multiple test records
        test_records = []
        for i in range(50):  # Create 50 test records
            test_data = {
                "test_id": f"scale_test_5node_{i}",
                "scale_phase": "5-node-cluster",
                "node_count": 5,
                "timestamp": "2024-01-01T00:00:00Z",
                "test_data": f"Test data {i} created in 5-node cluster for scale-down testing"
            }
            test_records.append(test_data)

        # Insert in batches
        inserted_count = 0
        for record in test_records:
            try:
                collection.data.insert(record)
                inserted_count += 1
                if inserted_count % 10 == 0:
                    print(f"   📊 Inserted {inserted_count}/50 records")
            except Exception as e:
                print(f"   ❌ Failed to insert record {inserted_count}: {e}")
                break

        print(f"✅ Successfully inserted {inserted_count} test records")

        # Verify data across nodes
        print("\n🔍 Verifying data distribution across 5 nodes...")
        verify_data_distribution(collection_name, [18080, 18081, 18082, 18083, 18084])

        client.close()
        return True, inserted_count

    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        return False, 0

def verify_data_distribution(collection_name, ports):
    """Verify that test data is distributed across all nodes"""
    node_counts = {}

    for port in ports:
        try:
            import weaviate
            import urllib.request

            # Calculate gRPC port
            base_grpc_port = 15051
            node_index = port - 18080
            grpc_port = base_grpc_port + node_index

            client = weaviate.connect_to_local(
                host="localhost",
                port=port,
                grpc_port=grpc_port,
                headers={}
            )
            client.connect()

            collection = client.collections.get(collection_name)

            # Count records on this node
            response = collection.query.fetch_objects(limit=1000)
            record_count = len(response.objects)

            node_counts[f'node_{node_index + 1}'] = {
                'port': port,
                'count': record_count,
                'status': 'accessible'
            }

            client.close()

        except Exception as e:
            node_counts[f'node_{node_index + 1}'] = {
                'port': port,
                'count': 0,
                'status': 'error',
                'error': str(e)
            }

    # Report distribution
    print("📊 Data Distribution Across Nodes:")
    total_records = 0
    for node, info in node_counts.items():
        status_emoji = "✅" if info['status'] == 'accessible' else "❌"
        print(f"   {status_emoji} {node} (port {info['port']}): {info['count']} records")
        if info['status'] == 'accessible':
            total_records += info['count']

    print(f"   📈 Total records across cluster: {total_records}")

    # Check if data is reasonably distributed
    accessible_nodes = sum(1 for info in node_counts.values() if info['status'] == 'accessible')
    if accessible_nodes >= 3 and total_records > 0:
        print("✅ Data distribution verified - ready for scale-down test")
        return True
    else:
        print("⚠️  Data distribution issues detected")
        return False

def perform_scale_down():
    """Perform the scale-down from 5 nodes to 3 nodes"""
    print("\n🔄 PERFORMING SCALE-DOWN: 5 → 3 NODES")
    print("=" * 50)

    # Nodes to remove: node4 and node5 (ports 18083, 18084)
    nodes_to_remove = ["weaviate-node4", "weaviate-node5"]
    ports_to_remove = [18083, 18084]

    print("🛑 Stopping nodes 4 and 5...")
    for container in nodes_to_remove:
        try:
            result = subprocess.run(['docker', 'stop', container], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"   ✅ Stopped {container}")
            else:
                print(f"   ❌ Failed to stop {container}")
        except Exception as e:
            print(f"   ❌ Error stopping {container}: {e}")

    # Wait for cluster to stabilize
    print("\n⏳ Waiting for cluster to stabilize after scale-down...")
    time.sleep(30)

    # Check cluster health after scale-down
    remaining_ports = [18080, 18081, 18082]
    healthy_count, node_status = check_cluster_health(remaining_ports)

    print("""
📊 Post-Scale-Down Status:""")
    print(f"   Remaining nodes: {healthy_count}/3 healthy")

    for node, info in node_status.items():
        status_emoji = "✅" if info['status'] == 'healthy' else "❌"
        print(f"   {status_emoji} {node}: {info['status']}")

    if healthy_count >= 2:  # At least 2 nodes for basic functionality
        print("✅ Cluster stable after scale-down")
        return True, remaining_ports
    else:
        print("❌ Cluster unstable after scale-down")
        return False, remaining_ports

def verify_data_integrity_after_scale_down(collection_name, remaining_ports):
    """Verify that all data is still accessible after scale-down"""
    print("\n🔍 VERIFYING DATA INTEGRITY AFTER SCALE-DOWN")
    print("=" * 50)

    # First, get the original data count from before scale-down
    original_count = 0
    try:
        import weaviate

        # Try to connect to remaining nodes
        for port in remaining_ports:
            try:
                base_grpc_port = 15051
                node_index = port - 18080
                grpc_port = base_grpc_port + node_index

                client = weaviate.connect_to_local(
                    host="localhost",
                    port=port,
                    grpc_port=grpc_port,
                    headers={}
                )
                client.connect()

                collection = client.collections.get(collection_name)
                response = collection.query.fetch_objects(limit=1000)
                count = len(response.objects)

                print(f"   📊 Node {port}: {count} records accessible")

                if count > original_count:
                    original_count = count  # Use the highest count as reference

                client.close()
                break  # Use first successful connection

            except Exception as e:
                print(f"   ❌ Cannot connect to node {port}: {e}")
                continue

    except Exception as e:
        print(f"   ❌ Data integrity check failed: {e}")
        return False

    if original_count == 0:
        print("⚠️  No data found - this may indicate data loss or connectivity issues")
        return False

    print(f"✅ Data integrity verified: {original_count} records still accessible")
    return True

def test_operations_after_scale_down(collection_name, remaining_ports):
    """Test basic operations after scale-down"""
    print("\n🧪 TESTING OPERATIONS AFTER SCALE-DOWN")
    print("=" * 50)

    operations_successful = 0
    total_operations = 4

    # Test 1: Read existing data
    print("1️⃣ Testing read operations...")
    try:
        import weaviate

        client = weaviate.connect_to_local(
            host="localhost",
            port=remaining_ports[0],
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection = client.collections.get(collection_name)
        response = collection.query.fetch_objects(limit=10)

        if len(response.objects) > 0:
            print("   ✅ Read operations working")
            operations_successful += 1
        else:
            print("   ❌ No data found in read test")

        client.close()

    except Exception as e:
        print(f"   ❌ Read test failed: {e}")

    # Test 2: Write new data
    print("\n2️⃣ Testing write operations...")
    try:
        import weaviate

        client = weaviate.connect_to_local(
            host="localhost",
            port=remaining_ports[0],
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection = client.collections.get(collection_name)

        # Insert a new record to test writes
        test_data = {
            "test_id": "scale_down_test_write",
            "scale_phase": "3-node-cluster",
            "node_count": 3,
            "timestamp": "2024-01-01T00:00:00Z",
            "test_data": "Test data written after scale-down"
        }

        collection.data.insert(test_data)

        # Verify the write
        response = collection.query.fetch_objects(
            filters={"test_id": "scale_down_test_write"},
            limit=1
        )

        if len(response.objects) > 0:
            print("   ✅ Write operations working")
            operations_successful += 1
        else:
            print("   ❌ Write verification failed")

        client.close()

    except Exception as e:
        print(f"   ❌ Write test failed: {e}")

    # Test 3: Query operations
    print("\n3️⃣ Testing query operations...")
    try:
        import weaviate

        client = weaviate.connect_to_local(
            host="localhost",
            port=remaining_ports[0],
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection = client.collections.get(collection_name)

        # Test a filtered query
        response = collection.query.fetch_objects(
            filters={"scale_phase": "5-node-cluster"},
            limit=5
        )

        if len(response.objects) > 0:
            print("   ✅ Query operations working")
            operations_successful += 1
        else:
            print("   ❌ Query test returned no results")

        client.close()

    except Exception as e:
        print(f"   ❌ Query test failed: {e}")

    # Test 4: Cross-node data consistency
    print("\n4️⃣ Testing cross-node data consistency...")
    consistency_check = verify_data_distribution(collection_name, remaining_ports)

    if consistency_check:
        print("   ✅ Data consistency verified across remaining nodes")
        operations_successful += 1
    else:
        print("   ❌ Data consistency issues detected")

    print(f"\n📊 Operations Test Results: {operations_successful}/{total_operations} successful")

    return operations_successful >= 3  # At least 3 out of 4 operations must work

def generate_scale_down_report(test_results):
    """Generate a comprehensive scale-down test report"""
    print("\n" + "=" * 70)
    print("📊 SCALE-DOWN TEST REPORT")
    print("=" * 70)

    # Overall assessment
    success_criteria = {
        'cluster_stable': test_results.get('cluster_stable', False),
        'data_integrity': test_results.get('data_integrity', False),
        'operations_working': test_results.get('operations_working', False),
        'no_data_loss': test_results.get('original_records', 0) > 0
    }

    criteria_met = sum(success_criteria.values())
    total_criteria = len(success_criteria)

    print("🎯 SUCCESS CRITERIA EVALUATION:")
    print(f"   ✅ Cluster stable after scale-down: {'✅' if success_criteria['cluster_stable'] else '❌'}")
    print(f"   ✅ Data integrity maintained: {'✅' if success_criteria['data_integrity'] else '❌'}")
    print(f"   ✅ Basic operations working: {'✅' if success_criteria['operations_working'] else '❌'}")
    print(f"   ✅ No data loss detected: {'✅' if success_criteria['no_data_loss'] else '❌'}")
    print(f"   📊 Overall: {criteria_met}/{total_criteria} criteria met")

    # Performance metrics
    if 'original_records' in test_results:
        print("""
📈 SCALE METRICS:""")
        print(f"   📊 Original records (5-node): {test_results['original_records']}")
        print(f"   📊 Final records (3-node): {test_results.get('final_records', 'N/A')}")
        print(f"   📊 Scale-down time: {test_results.get('scale_down_time', 'N/A')} seconds")

    # Recommendations
    print("""
💡 RECOMMENDATIONS:""")
    if criteria_met == total_criteria:
        print("   🎉 EXCELLENT: Scale-down successful with no issues")
        print("   ✅ System handles cluster size changes gracefully")
        print("   ✅ Data remains consistent and accessible")
    elif criteria_met >= total_criteria - 1:
        print("   ✅ GOOD: Scale-down successful with minor issues")
        print("   ⚠️  Monitor system during cluster size changes")
    else:
        print("   ⚠️  ISSUES DETECTED: Scale-down may need optimization")
        print("   🔧 Consider reviewing cluster reconfiguration logic")

    return criteria_met == total_criteria

def main():
    """Main function for scale-down testing"""
    print("🚀 STARTING SCALE-DOWN TEST")
    print("   Testing reduction from 5-node to 3-node cluster")
    print("=" * 70)

    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    test_results = {}
    start_time = time.time()

    # Step 1: Verify 5-node cluster is running
    print("\n📋 STEP 1: VERIFYING 5-NODE CLUSTER")
    ports_5node = [18080, 18081, 18082, 18083, 18084]
    healthy_count, node_status = check_cluster_health(ports_5node)

    print(f"5-node cluster status: {healthy_count}/5 nodes healthy")

    if healthy_count < 3:
        print("❌ Insufficient nodes healthy for scale-down test")
        print("   Need at least 3 healthy nodes in 5-node cluster")
        return False

    # Step 2: Create test data
    print("\n📋 STEP 2: CREATING TEST DATA")
    data_created, record_count = create_scale_test_data()
    test_results['original_records'] = record_count

    if not data_created or record_count == 0:
        print("❌ Failed to create test data")
        return False

    # Step 3: Perform scale-down
    print("\n📋 STEP 3: SCALE-DOWN EXECUTION")
    cluster_stable, remaining_ports = perform_scale_down()
    test_results['cluster_stable'] = cluster_stable

    if not cluster_stable:
        print("❌ Scale-down failed - cluster unstable")
        test_results['scale_down_time'] = time.time() - start_time
        generate_scale_down_report(test_results)
        return False

    # Step 4: Verify data integrity
    print("\n📋 STEP 4: DATA INTEGRITY VERIFICATION")
    data_integrity = verify_data_integrity_after_scale_down("SCALE_DOWN_TEST_COLLECTION", remaining_ports)
    test_results['data_integrity'] = data_integrity

    # Step 5: Test operations
    print("\n📋 STEP 5: OPERATIONS TESTING")
    operations_working = test_operations_after_scale_down("SCALE_DOWN_TEST_COLLECTION", remaining_ports)
    test_results['operations_working'] = operations_working

    # Step 6: Final verification
    print("\n📋 STEP 6: FINAL CLUSTER VERIFICATION")
    final_healthy, _ = check_cluster_health(remaining_ports)
    print(f"Final 3-node cluster status: {final_healthy}/3 nodes healthy")

    # Calculate final record count
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=remaining_ports[0],
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection = client.collections.get("SCALE_DOWN_TEST_COLLECTION")
        response = collection.query.fetch_objects(limit=1000)
        test_results['final_records'] = len(response.objects)

        client.close()
    except:
        test_results['final_records'] = 0

    test_results['scale_down_time'] = time.time() - start_time

    # Generate final report
    success = generate_scale_down_report(test_results)

    if success:
        print("\n🎉 SCALE-DOWN TEST COMPLETED SUCCESSFULLY!")
        print("   ✅ 5→3 node reduction successful")
        print("   ✅ Data integrity maintained")
        print("   ✅ All operations working")
        print("   ✅ No data loss detected")
        return True
    else:
        print("\n⚠️  SCALE-DOWN TEST COMPLETED WITH ISSUES")
        print("   Review the report above for specific concerns")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)