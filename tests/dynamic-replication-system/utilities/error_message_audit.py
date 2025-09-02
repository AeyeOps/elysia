#!/usr/bin/env python3
"""
error_message_audit.py - Collect and analyze error messages for clarity
"""

import sys
import os
import uuid
import time
import json
import re
import urllib.request
from collections import defaultdict
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

class ErrorAuditor:
    """Class to collect and analyze error messages"""

    def __init__(self):
        self.errors = []
        self.error_categories = defaultdict(list)

    def add_error(self, scenario, error_msg, expected=False):
        """Add an error to the audit"""
        error_data = {
            'scenario': scenario,
            'message': error_msg,
            'expected': expected,
            'timestamp': time.time(),
            'category': self.categorize_error(error_msg)
        }

        self.errors.append(error_data)
        self.error_categories[error_data['category']].append(error_data)

    def categorize_error(self, error_msg):
        """Categorize error messages"""
        msg_lower = error_msg.lower()

        if 'leader not found' in msg_lower:
            return 'leadership'
        elif 'resolve node name' in msg_lower or 'node' in msg_lower:
            return 'networking'
        elif 'collection' in msg_lower and ('not exist' in msg_lower or 'not found' in msg_lower):
            return 'collection_not_found'
        elif 'property' in msg_lower:
            return 'property_error'
        elif 'data type' in msg_lower or 'datatype' in msg_lower:
            return 'data_type_error'
        elif 'connection' in msg_lower:
            return 'connection_error'
        elif 'timeout' in msg_lower:
            return 'timeout_error'
        elif 'permission' in msg_lower or 'access' in msg_lower:
            return 'permission_error'
        elif 'invalid' in msg_lower:
            return 'validation_error'
        else:
            return 'other'

    def analyze_error_messages(self):
        """Analyze collected error messages"""
        analysis = {
            'total_errors': len(self.errors),
            'expected_errors': len([e for e in self.errors if e['expected']]),
            'unexpected_errors': len([e for e in self.errors if not e['expected']]),
            'categories': dict(self.error_categories),
            'quality_score': self.calculate_quality_score()
        }

        return analysis

    def calculate_quality_score(self):
        """Calculate a quality score for error messages"""
        if not self.errors:
            return 100  # No errors is perfect

        score = 0
        total_weight = 0

        for error in self.errors:
            msg = error['message']
            weight = 1

            # Check for clear, actionable messages
            if len(msg) > 10:  # Not too short
                score += 20
            if any(word in msg.lower() for word in ['check', 'verify', 'ensure', 'use', 'try']):  # Actionable
                score += 30
            if not msg.startswith('error:') and not msg.startswith('failed'):  # Not generic
                score += 20
            if re.search(r'\d+', msg):  # Contains specific information
                score += 15
            if len(msg.split()) > 3:  # Has some detail
                score += 15

            total_weight += weight

        return min(100, int((score / total_weight) * 100)) if total_weight > 0 else 100

    def print_report(self):
        """Print a comprehensive error audit report"""
        analysis = self.analyze_error_messages()

        print("\n" + "=" * 70)
        print("📊 ERROR MESSAGE AUDIT REPORT")
        print("=" * 70)

        print(f"📈 Total Errors Analyzed: {analysis['total_errors']}")
        print(f"✅ Expected Errors: {analysis['expected_errors']}")
        print(f"❌ Unexpected Errors: {analysis['unexpected_errors']}")
        print(f"🎯 Quality Score: {analysis['quality_score']}/100")

        if analysis['quality_score'] >= 80:
            print("   ✅ Excellent error message quality")
        elif analysis['quality_score'] >= 60:
            print("   ⚠️  Good error message quality")
        else:
            print("   ❌ Poor error message quality - needs improvement")

        print("\n📋 Error Categories:")
        for category, errors in analysis['categories'].items():
            print(f"   • {category}: {len(errors)} errors")

        print("\n🔍 Sample Error Messages:")
        for i, error in enumerate(self.errors[:5]):  # Show first 5
            status = "✅" if error['expected'] else "❌"
            print(f"   {status} {error['scenario']}: {error['message'][:80]}...")

        if len(self.errors) > 5:
            print(f"   ... and {len(self.errors) - 5} more errors")

def test_error_scenarios(auditor):
    """Test various error scenarios and collect messages"""

    print("🧪 COLLECTING ERROR SCENARIOS")
    print("=" * 50)

    # Scenario 1: Non-existent collection
    print("\n1️⃣ Testing non-existent collection access")
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection = client.collections.get("NON_EXISTENT_COLLECTION_12345")
        response = collection.query.fetch_objects(limit=1)
        print("   ❌ Unexpected success")
        auditor.add_error("non_existent_collection", "No error occurred", expected=False)

        client.close()

    except Exception as e:
        error_msg = str(e)
        print(f"   ✅ Expected error: {error_msg[:100]}...")
        auditor.add_error("non_existent_collection", error_msg, expected=True)

    # Scenario 2: Invalid data type
    print("\n2️⃣ Testing invalid data type")
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection_name = f"INVALID_TYPE_TEST_{str(uuid.uuid4())[:8]}"
        collection = client.collections.create(
            name=collection_name,
            properties=[
                Property(name="test_prop", data_type="INVALID_TYPE"),
            ]
        )
        print("   ❌ Unexpected success with invalid type")
        auditor.add_error("invalid_data_type", "No error occurred", expected=False)

        client.close()

    except Exception as e:
        error_msg = str(e)
        print(f"   ✅ Expected error: {error_msg[:100]}...")
        auditor.add_error("invalid_data_type", error_msg, expected=True)

    # Scenario 3: Network connectivity issue
    print("\n3️⃣ Testing network connectivity (stopping node)")
    try:
        import subprocess
        # Stop a node temporarily
        subprocess.run(["docker", "stop", "phase4-test-node3-1"],
                      capture_output=True, timeout=30)

        time.sleep(5)  # Wait for node to go down

        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18082,  # Stopped node
            grpc_port=15053,
            headers={}
        )
        client.connect()

        collection = client.collections.get("ELYSIA_CONFIG")
        response = collection.query.fetch_objects(limit=1)

        print("   ❌ Unexpected success with stopped node")
        auditor.add_error("network_connectivity", "No error occurred", expected=False)

        client.close()

    except Exception as e:
        error_msg = str(e)
        print(f"   ✅ Expected error: {error_msg[:100]}...")
        auditor.add_error("network_connectivity", error_msg, expected=True)

    # Restart the node
    subprocess.run(["docker", "start", "phase4-test-node3-1"],
                  capture_output=True, timeout=30)
    time.sleep(10)

    # Scenario 4: Invalid property name
    print("\n4️⃣ Testing invalid property name")
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection_name = f"INVALID_PROP_TEST_{str(uuid.uuid4())[:8]}"
        collection = client.collections.create(
            name=collection_name,
            properties=[
                Property(name="", data_type=DataType.TEXT),  # Empty name
            ]
        )
        print("   ❌ Unexpected success with empty property name")
        auditor.add_error("invalid_property_name", "No error occurred", expected=False)

        client.close()

    except Exception as e:
        error_msg = str(e)
        print(f"   ✅ Expected error: {error_msg[:100]}...")
        auditor.add_error("invalid_property_name", error_msg, expected=True)

    # Scenario 5: Duplicate collection creation
    print("\n5️⃣ Testing duplicate collection creation")
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection_name = f"DUPLICATE_TEST_{str(uuid.uuid4())[:8]}"

        # Create collection first time
        collection = client.collections.create(
            name=collection_name,
            properties=[
                Property(name="test_prop", data_type=DataType.TEXT),
            ]
        )

        # Try to create again
        collection2 = client.collections.create(
            name=collection_name,
            properties=[
                Property(name="test_prop", data_type=DataType.TEXT),
            ]
        )

        print("   ❌ Unexpected success with duplicate collection")
        auditor.add_error("duplicate_collection", "No error occurred", expected=False)

        # Clean up
        client.collections.delete(collection_name)
        client.close()

    except Exception as e:
        error_msg = str(e)
        print(f"   ✅ Expected error: {error_msg[:100]}...")
        auditor.add_error("duplicate_collection", error_msg, expected=True)

    # Scenario 6: Invalid query syntax
    print("\n6️⃣ Testing invalid query syntax")
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection = client.collections.get("ELYSIA_CONFIG")
        # Try invalid filter
        response = collection.query.fetch_objects(
            filters="invalid_syntax_here"
        )

        print("   ❌ Unexpected success with invalid query")
        auditor.add_error("invalid_query_syntax", "No error occurred", expected=False)

        client.close()

    except Exception as e:
        error_msg = str(e)
        print(f"   ✅ Expected error: {error_msg[:100]}...")
        auditor.add_error("invalid_query_syntax", error_msg, expected=True)

    # Scenario 7: Resource exhaustion (large request)
    print("\n7️⃣ Testing resource exhaustion")
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection = client.collections.get("ELYSIA_CONFIG")

        # Try to fetch a huge number of objects
        response = collection.query.fetch_objects(limit=1000000)

        print("   ⚠️  Large query succeeded (may indicate lack of limits)")
        auditor.add_error("resource_exhaustion", f"Query returned {len(response.objects)} objects", expected=False)

        client.close()

    except Exception as e:
        error_msg = str(e)
        print(f"   ✅ Expected error: {error_msg[:100]}...")
        auditor.add_error("resource_exhaustion", error_msg, expected=True)

def main():
    """Main function for error message audit"""
    print("🚀 STARTING ERROR MESSAGE AUDIT")
    print("   Collecting and analyzing error messages for clarity")
    print("=" * 70)

    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Check cluster health
    ports = [18080, 18081, 18082]
    healthy_nodes = sum(1 for port in ports if check_node_health(port))
    print(f"📊 Cluster Status: {healthy_nodes}/{len(ports)} nodes healthy")

    if healthy_nodes < 2:
        print("⚠️  WARNING: Need at least 2 healthy nodes for comprehensive error testing")
        if healthy_nodes < 1:
            print("❌ Cannot proceed - no healthy nodes")
            return False

    # Initialize auditor
    auditor = ErrorAuditor()

    # Run error scenarios
    test_error_scenarios(auditor)

    # Generate and print report
    auditor.print_report()

    # Additional analysis
    analysis = auditor.analyze_error_messages()

    print("\n🎯 RECOMMENDATIONS:")
    if analysis['quality_score'] < 60:
        print("   ❌ CRITICAL: Error messages need significant improvement")
        print("      • Add specific error codes")
        print("      • Include actionable guidance")
        print("      • Provide context about what went wrong")
    elif analysis['quality_score'] < 80:
        print("   ⚠️  MODERATE: Error messages could be clearer")
        print("      • Add more specific details")
        print("      • Include troubleshooting suggestions")
    else:
        print("   ✅ GOOD: Error messages are clear and actionable")

    # Check for common issues
    leadership_errors = len(analysis['categories'].get('leadership', []))
    if leadership_errors > 0:
        print(f"   📋 Found {leadership_errors} leadership-related errors")
        print("      • Consider improving cluster coordination messages")

    networking_errors = len(analysis['categories'].get('networking', []))
    if networking_errors > 0:
        print(f"   📋 Found {networking_errors} networking-related errors")
        print("      • Consider adding network troubleshooting guidance")

    # Overall assessment
    success = analysis['quality_score'] >= 60 and analysis['unexpected_errors'] == 0

    if success:
        print("\n🎉 ERROR MESSAGE AUDIT PASSED")
        print("   ✅ Error messages are clear and actionable")
        print("   ✅ No unexpected errors detected")
        print("   ✅ Good user experience for error scenarios")
        return True
    else:
        print("\n⚠️  ERROR MESSAGE AUDIT COMPLETED WITH ISSUES")
        if analysis['quality_score'] < 60:
            print("   ❌ Error message quality needs improvement")
        if analysis['unexpected_errors'] > 0:
            print("   ❌ Unexpected errors detected - investigate system behavior")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)