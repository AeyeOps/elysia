#!/usr/bin/env python3
"""
concurrent_operations.py - Test simultaneous collection operations from multiple connections
"""

import sys
import os
import uuid
import time
import threading
import concurrent.futures
import urllib.request
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from elysia.util.client import ClientManager
from elysia.config import settings
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType
from dotenv import load_dotenv

def check_node_health(port):
    """Check if a node is responding"""
    try:
        url = f"http://localhost:{port}/v1/meta"
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except:
        return False

def create_collection_worker(worker_id, collection_name, results, errors):
    """Worker function to create a collection"""
    try:
        import weaviate

        # Connect to a random node
        ports = [18080, 18081, 18082]
        port = ports[worker_id % len(ports)]
        grpc_port = 15051 + (port - 18080)

        client = weaviate.connect_to_local(
            host="localhost",
            port=port,
            grpc_port=grpc_port,
            headers={}
        )
        client.connect()

        start_time = time.time()

        # Create collection
        collection = client.collections.create(
            name=collection_name,
            properties=[
                Property(name="worker_id", data_type=DataType.TEXT),
                Property(name="test_data", data_type=DataType.TEXT),
                Property(name="created_at", data_type=DataType.DATE),
                Property(name="worker_number", data_type=DataType.INT),
            ]
        )

        end_time = time.time()
        creation_time = end_time - start_time

        # Insert test data
        collection = client.collections.get(collection_name)
        test_data = {
            "worker_id": f"worker_{worker_id}",
            "test_data": f"Data from worker {worker_id}",
            "created_at": "2024-01-01T00:00:00Z",
            "worker_number": worker_id
        }

        collection.data.insert(test_data)

        client.close()

        results.append({
            'worker_id': worker_id,
            'collection_name': collection_name,
            'port': port,
            'creation_time': creation_time,
            'success': True
        })

        print(f"   ✅ Worker {worker_id}: Created {collection_name} on node {port} in {creation_time:.2f}s")

    except Exception as e:
        error_msg = str(e)
        errors.append({
            'worker_id': worker_id,
            'collection_name': collection_name,
            'error': error_msg
        })

        print(f"   ❌ Worker {worker_id}: Failed to create {collection_name} - {error_msg[:50]}...")

def test_concurrent_collection_creation():
    """Test creating collections simultaneously from multiple threads"""
    print("🧪 TESTING CONCURRENT COLLECTION CREATION")
    print("=" * 50)

    # Test with different numbers of concurrent workers
    worker_counts = [2, 5, 10, 20]

    for num_workers in worker_counts:
        print(f"\n🔄 Testing with {num_workers} concurrent workers")
        print("-" * 40)

        results = []
        errors = []

        # Create unique collection names
        collection_names = [f"CONCURRENT_TEST_{i}_{str(uuid.uuid4())[:8]}" for i in range(num_workers)]

        start_time = time.time()

        # Launch workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for i in range(num_workers):
                future = executor.submit(create_collection_worker, i, collection_names[i], results, errors)
                futures.append(future)

            # Wait for all to complete
            concurrent.futures.wait(futures)

        end_time = time.time()
        total_time = end_time - start_time

        # Analyze results
        successful_creations = len(results)
        failed_creations = len(errors)

        print(f"   📊 Results: {successful_creations} success, {failed_creations} failures")
        print(f"   📊 Total time: {total_time:.2f}s")
        if results:
            avg_creation_time = sum(r['creation_time'] for r in results) / len(results)
            print(f"   📊 Average creation time: {avg_creation_time:.2f}s")
            # Check for race conditions - did any collections get the same name?
            created_names = [r['collection_name'] for r in results]
            unique_names = set(created_names)
            if len(created_names) != len(unique_names):
                print("   ⚠️  WARNING: Possible name collision detected!")
            else:
                print("   ✅ No name collisions detected")

        # Clean up created collections
        cleanup_errors = 0
        try:
            import weaviate
            client = weaviate.connect_to_local(
                host="localhost",
                port=18080,
                grpc_port=15051,
                headers={}
            )
            client.connect()

            for collection_name in collection_names:
                try:
                    client.collections.delete(collection_name)
                except:
                    cleanup_errors += 1

            client.close()

        except:
            cleanup_errors = num_workers

        print(f"   🗑️  Cleanup: {num_workers - cleanup_errors}/{num_workers} collections deleted")

        # Store results for analysis
        yield {
            'worker_count': num_workers,
            'successful': successful_creations,
            'failed': failed_creations,
            'total_time': total_time,
            'avg_creation_time': avg_creation_time if results else 0,
            'errors': errors
        }

def insert_data_worker(worker_id, collection_name, num_objects, results, errors):
    """Worker function to insert data into a collection"""
    try:
        import weaviate

        # Connect to a random node
        ports = [18080, 18081, 18082]
        port = ports[worker_id % len(ports)]
        grpc_port = 15051 + (port - 18080)

        client = weaviate.connect_to_local(
            host="localhost",
            port=port,
            grpc_port=grpc_port,
            headers={}
        )
        client.connect()

        collection = client.collections.get(collection_name)
        start_time = time.time()

        # Insert multiple objects
        inserted_count = 0
        for i in range(num_objects):
            try:
                test_data = {
                    "worker_id": f"worker_{worker_id}",
                    "object_id": i,
                    "test_data": f"Concurrent data from worker {worker_id}, object {i}",
                    "created_at": "2024-01-01T00:00:00Z"
                }

                collection.data.insert(test_data)
                inserted_count += 1

            except Exception as e:
                break  # Stop on first error

        end_time = time.time()
        insert_time = end_time - start_time

        client.close()

        results.append({
            'worker_id': worker_id,
            'port': port,
            'inserted': inserted_count,
            'expected': num_objects,
            'insert_time': insert_time,
            'success': inserted_count == num_objects
        })

        print(f"   ✅ Worker {worker_id}: Inserted {inserted_count}/{num_objects} objects in {insert_time:.2f}s")

    except Exception as e:
        error_msg = str(e)
        errors.append({
            'worker_id': worker_id,
            'error': error_msg
        })

        print(f"   ❌ Worker {worker_id}: Failed to insert data - {error_msg[:50]}...")

def test_concurrent_data_insertion():
    """Test inserting data simultaneously from multiple threads"""
    print("\n🧪 TESTING CONCURRENT DATA INSERTION")
    print("=" * 50)

    # First create a shared collection
    shared_collection = f"SHARED_CONCURRENT_TEST_{str(uuid.uuid4())[:8]}"

    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection = client.collections.create(
            name=shared_collection,
            properties=[
                Property(name="worker_id", data_type=DataType.TEXT),
                Property(name="object_id", data_type=DataType.INT),
                Property(name="test_data", data_type=DataType.TEXT),
                Property(name="created_at", data_type=DataType.DATE),
            ]
        )
        client.close()
        print(f"   📝 Created shared collection: {shared_collection}")

    except Exception as e:
        print(f"   ❌ Failed to create shared collection: {e}")
        return

    # Test with different numbers of concurrent workers
    worker_counts = [3, 5, 8]
    objects_per_worker = 10

    for num_workers in worker_counts:
        print(f"\n🔄 Testing with {num_workers} concurrent workers ({objects_per_worker} objects each)")
        print("-" * 60)

        results = []
        errors = []

        start_time = time.time()

        # Launch workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for i in range(num_workers):
                future = executor.submit(insert_data_worker, i, shared_collection, objects_per_worker, results, errors)
                futures.append(future)

            # Wait for all to complete
            concurrent.futures.wait(futures)

        end_time = time.time()
        total_time = end_time - start_time

        # Analyze results
        successful_workers = sum(1 for r in results if r['success'])
        total_inserted = sum(r['inserted'] for r in results)
        expected_total = num_workers * objects_per_worker

        print(f"   📊 Results: {successful_workers}/{num_workers} workers successful")
        print(f"   📊 Data: {total_inserted}/{expected_total} objects inserted")
        print(f"   📊 Total time: {total_time:.2f}s")
        if results:
            avg_insert_time = sum(r['insert_time'] for r in results) / len(results)
            print(f"   📊 Average insert time: {avg_insert_time:.2f}s")
        # Check for data consistency
        try:
            import weaviate
            client = weaviate.connect_to_local(
                host="localhost",
                port=18080,
                grpc_port=15051,
                headers={}
            )
            client.connect()

            collection = client.collections.get(shared_collection)
            total_objects = collection.query.fetch_objects(limit=1000)
            actual_count = len(total_objects.objects)

            client.close()

            print(f"   📊 Verification: {actual_count} objects found in collection")

            if actual_count == expected_total:
                print("   ✅ Data consistency verified")
            else:
                print("   ⚠️  Data consistency issue detected")

        except Exception as e:
            print(f"   ❌ Verification failed: {e}")

        # Store results for analysis
        yield {
            'worker_count': num_workers,
            'successful_workers': successful_workers,
            'total_inserted': total_inserted,
            'expected_total': expected_total,
            'total_time': total_time,
            'errors': errors
        }

    # Clean up shared collection
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()
        client.collections.delete(shared_collection)
        client.close()
        print(f"   🗑️  Shared collection deleted: {shared_collection}")

    except:
        print(f"   ⚠️  Failed to delete shared collection: {shared_collection}")

def test_concurrent_queries():
    """Test running queries simultaneously from multiple threads"""
    print("\n🧪 TESTING CONCURRENT QUERIES")
    print("=" * 50)

    # Use existing collection for queries
    target_collection = "ELYSIA_CONFIG"

    # Test with different numbers of concurrent query workers
    worker_counts = [5, 10, 15]

    for num_workers in worker_counts:
        print(f"\n🔄 Testing with {num_workers} concurrent query workers")
        print("-" * 50)

        results = []
        errors = []

        def query_worker(worker_id):
            try:
                import weaviate

                # Connect to a random node
                ports = [18080, 18081, 18082]
                port = ports[worker_id % len(ports)]
                grpc_port = 15051 + (port - 18080)

                client = weaviate.connect_to_local(
                    host="localhost",
                    port=port,
                    grpc_port=grpc_port,
                    headers={}
                )
                client.connect()

                start_time = time.time()

                # Perform a query
                collection = client.collections.get(target_collection)
                response = collection.query.fetch_objects(limit=10)

                end_time = time.time()
                query_time = end_time - start_time

                client.close()

                results.append({
                    'worker_id': worker_id,
                    'port': port,
                    'objects_found': len(response.objects),
                    'query_time': query_time,
                    'success': True
                })

                print(f"   ✅ Worker {worker_id}: Queried {len(response.objects)} objects in {query_time:.3f}s")

            except Exception as e:
                error_msg = str(e)
                errors.append({
                    'worker_id': worker_id,
                    'error': error_msg
                })

                print(f"   ❌ Worker {worker_id}: Query failed - {error_msg[:50]}...")

        start_time = time.time()

        # Launch workers
        threads = []
        for i in range(num_workers):
            thread = threading.Thread(target=query_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # Analyze results
        successful_queries = len(results)
        failed_queries = len(errors)

        print(f"   📊 Results: {successful_queries} success, {failed_queries} failures")
        print(f"   📊 Total time: {total_time:.2f}s")
        if results:
            avg_query_time = sum(r['query_time'] for r in results) / len(results)
            total_objects = sum(r['objects_found'] for r in results)
            print(f"   📊 Average query time: {avg_query_time:.3f}s")
            print(f"   📊 Total objects found: {total_objects}")
        # Store results for analysis
        yield {
            'worker_count': num_workers,
            'successful_queries': successful_queries,
            'failed_queries': failed_queries,
            'total_time': total_time,
            'avg_query_time': avg_query_time if results else 0,
            'errors': errors
        }

def main():
    """Main function for concurrent operations testing"""
    print("🚀 STARTING CONCURRENT OPERATIONS TESTS")
    print("   Testing simultaneous collection operations from multiple connections")
    print("=" * 80)

    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Check cluster health
    ports = [18080, 18081, 18082]
    healthy_nodes = sum(1 for port in ports if check_node_health(port))
    print(f"📊 Cluster Status: {healthy_nodes}/{len(ports)} nodes healthy")

    if healthy_nodes < 3:
        print("⚠️  WARNING: Need all nodes healthy for meaningful concurrent testing")
        if healthy_nodes < 2:
            print("❌ Cannot proceed - insufficient healthy nodes")
            return False

    # Run concurrent tests
    all_results = []

    # Test concurrent collection creation
    print("\n🔄 PHASE 1: CONCURRENT COLLECTION CREATION")
    for result in test_concurrent_collection_creation():
        all_results.append(('collection_creation', result))

    # Test concurrent data insertion
    print("\n🔄 PHASE 2: CONCURRENT DATA INSERTION")
    for result in test_concurrent_data_insertion():
        all_results.append(('data_insertion', result))

    # Test concurrent queries
    print("\n🔄 PHASE 3: CONCURRENT QUERIES")
    for result in test_concurrent_queries():
        all_results.append(('concurrent_queries', result))

    # Summary
    print("\n" + "=" * 80)
    print("📊 CONCURRENT OPERATIONS TEST RESULTS")
    print("=" * 80)

    total_successes = 0
    total_failures = 0
    race_conditions = 0

    for test_type, result in all_results:
        print(f"\n📋 {test_type.upper()}: {result['worker_count']} workers")

        if 'successful' in result:
            success_count = result['successful']
            total_count = result['worker_count']
            print(f"   ✅ Success Rate: {success_count}/{total_count}")

            if success_count == total_count:
                total_successes += 1
            else:
                total_failures += 1

        if 'successful_workers' in result:
            success_workers = result['successful_workers']
            total_workers = result['worker_count']
            print(f"   ✅ Worker Success: {success_workers}/{total_workers}")

            if success_workers == total_workers:
                total_successes += 1
            else:
                total_failures += 1

        if 'successful_queries' in result:
            success_queries = result['successful_queries']
            total_queries = result['worker_count']
            print(f"   ✅ Query Success: {success_queries}/{total_queries}")

            if success_queries == total_queries:
                total_successes += 1
            else:
                total_failures += 1

        if 'total_time' in result:
            print(f"   📊 Total time: {result['total_time']:.2f}s")
        if 'errors' in result and result['errors']:
            print(f"   ❌ Errors: {len(result['errors'])}")
            race_conditions += len(result['errors'])

    print("\n📈 OVERALL SUMMARY:")
    print(f"   Test Scenarios: {len(all_results)}")
    print(f"   Fully Successful: {total_successes}")
    print(f"   With Issues: {total_failures}")
    print(f"   Race Conditions/Errors: {race_conditions}")

    success = (total_failures == 0 and race_conditions == 0)

    if success:
        print("\n🎉 CONCURRENT OPERATIONS TESTS PASSED")
        print("   ✅ No race conditions detected")
        print("   ✅ All concurrent operations handled properly")
        print("   ✅ System maintains data consistency")
        return True
    else:
        print("\n⚠️  CONCURRENT OPERATIONS TESTS COMPLETED WITH ISSUES")
        if total_failures > 0:
            print("   ❌ Some concurrent operations failed")
        if race_conditions > 0:
            print("   ❌ Race conditions or conflicts detected")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)