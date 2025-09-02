#!/usr/bin/env python3
"""
production_monitor.py - Continuous cluster monitoring for production
"""

import sys
import os
import time
import json
import threading
from datetime import datetime
import psutil

# Add the elysia path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

def get_cluster_status():
    """Get current cluster health status"""
    ports = [18080, 18081, 18082]
    healthy_nodes = 0
    node_details = []

    for port in ports:
        try:
            import urllib.request
            url = f"http://localhost:{port}/v1/meta"
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    healthy_nodes += 1
                    node_details.append(f"✅ Node {port}: Healthy")
                else:
                    node_details.append(f"⚠️ Node {port}: Status {response.status}")
        except Exception as e:
            node_details.append(f"❌ Node {port}: {str(e)[:50]}...")

    return {
        'healthy_count': healthy_nodes,
        'total_count': len(ports),
        'node_details': node_details,
        'overall_status': 'healthy' if healthy_nodes >= 2 else 'degraded' if healthy_nodes >= 1 else 'critical'
    }

def get_system_resources():
    """Get system resource usage"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
        'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'disk_usage_percent': psutil.disk_usage('/').percent
    }

def test_cluster_performance():
    """Test basic cluster performance metrics"""
    try:
        import weaviate

        # Test basic connectivity
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        # Test collection access
        collections = client.collections.list_all()
        collection_count = len(collections)

        # Test basic query performance
        start_time = time.time()
        if collections:
            collection = client.collections.get(list(collections.keys())[0])
            response = collection.query.fetch_objects(limit=10)
            query_time = time.time() - start_time
            record_count = len(response.objects)
        else:
            query_time = 0
            record_count = 0

        client.close()

        return {
            'status': 'success',
            'collections': collection_count,
            'query_time': round(query_time, 4),
            'sample_records': record_count
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)[:100]
        }

def log_monitoring_data(data):
    """Log monitoring data to file"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        'timestamp': timestamp,
        'cluster': data['cluster'],
        'system': data['system'],
        'performance': data['performance']
    }

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), 'monitoring_logs')
    os.makedirs(log_dir, exist_ok=True)

    # Write to daily log file
    date_str = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'cluster_monitoring_{date_str}.jsonl')

    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def print_status_report(data):
    """Print current status to console"""
    print(f"\n📊 CLUSTER MONITORING REPORT - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)

    # Cluster status
    cluster = data['cluster']
    print(f"🔗 Cluster Status: {cluster['healthy_count']}/{cluster['total_count']} nodes healthy")
    for detail in cluster['node_details']:
        print(f"   {detail}")

    # System resources
    system = data['system']
    print("""
💻 System Resources:""")
    print(".1f")
    print(".1f")
    print(".1f")

    # Performance
    perf = data['performance']
    if perf['status'] == 'success':
        print("""
⚡ Performance:""")
        print(f"   📊 Collections available: {perf['collections']}")
        print(".4f")
        print(f"   📊 Sample records found: {perf['sample_records']}")
    else:
        print(f"   ❌ Performance test failed: {perf['error']}")

    # Overall assessment
    cluster_healthy = cluster['overall_status'] == 'healthy'
    system_healthy = system['cpu_percent'] < 80 and system['memory_percent'] < 80
    performance_healthy = perf['status'] == 'success'

    if cluster_healthy and system_healthy and performance_healthy:
        print("\n✅ OVERALL STATUS: HEALTHY")
    elif cluster_healthy or system_healthy:
        print("\n⚠️  OVERALL STATUS: DEGRADED")
    else:
        print("\n❌ OVERALL STATUS: CRITICAL")

def monitoring_loop(interval_seconds=60):
    """Main monitoring loop"""
    print("🚀 STARTING PRODUCTION CLUSTER MONITORING")
    print(f"   Monitoring interval: {interval_seconds} seconds")
    print("=" * 60)

    try:
        while True:
            # Collect all monitoring data
            monitoring_data = {
                'cluster': get_cluster_status(),
                'system': get_system_resources(),
                'performance': test_cluster_performance()
            }

            # Log data
            log_monitoring_data(monitoring_data)

            # Print status report
            print_status_report(monitoring_data)

            # Wait for next interval
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")

def generate_monitoring_report():
    """Generate a summary report from monitoring logs"""
    print("📊 GENERATING MONITORING REPORT")
    print("=" * 40)

    log_dir = os.path.join(os.path.dirname(__file__), 'monitoring_logs')
    if not os.path.exists(log_dir):
        print("❌ No monitoring logs found")
        return

    # Read today's log file
    date_str = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'cluster_monitoring_{date_str}.jsonl')

    if not os.path.exists(log_file):
        print("❌ Today's monitoring log not found")
        return

    # Parse log entries
    entries = []
    with open(log_file, 'r') as f:
        for line in f:
            try:
                entries.append(json.loads(line.strip()))
            except:
                continue

    if not entries:
        print("❌ No valid log entries found")
        return

    print(f"📈 Analyzing {len(entries)} monitoring entries from today")

    # Analyze data
    cluster_health_scores = []
    cpu_usage = []
    memory_usage = []
    query_times = []

    for entry in entries:
        # Cluster health (0-1 scale)
        cluster = entry['cluster']
        health_score = cluster['healthy_count'] / cluster['total_count']
        cluster_health_scores.append(health_score)

        # System resources
        system = entry['system']
        cpu_usage.append(system['cpu_percent'])
        memory_usage.append(system['memory_percent'])

        # Performance
        perf = entry['performance']
        if perf['status'] == 'success':
            query_times.append(perf['query_time'])

    # Calculate statistics
    avg_cluster_health = sum(cluster_health_scores) / len(cluster_health_scores) if cluster_health_scores else 0
    avg_cpu = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
    avg_memory = sum(memory_usage) / len(memory_usage) if memory_usage else 0
    avg_query_time = sum(query_times) / len(query_times) if query_times else 0

    # Generate report
    print("""
📋 DAILY MONITORING SUMMARY""")
    print(".1f")
    print(".1f")
    print(".1f")
    if query_times:
        print(".4f")

    # Recommendations
    print("""
💡 RECOMMENDATIONS""")
    if avg_cluster_health < 0.8:
        print("   ⚠️  Cluster health is degraded - investigate node issues")
    if avg_cpu > 70:
        print("   ⚠️  High CPU usage detected - consider resource scaling")
    if avg_memory > 70:
        print("   ⚠️  High memory usage detected - monitor for memory leaks")
    if avg_query_time > 0.5:
        print("   ⚠️  Query performance is slow - investigate database optimization")

    if avg_cluster_health >= 0.8 and avg_cpu <= 70 and avg_memory <= 70:
        print("   ✅ System is performing well within normal parameters")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == 'report':
        # Generate monitoring report
        generate_monitoring_report()
    else:
        # Start continuous monitoring
        interval = 60  # Default 1 minute
        if len(sys.argv) > 1:
            try:
                interval = int(sys.argv[1])
            except:
                print("❌ Invalid interval specified, using default 60 seconds")

        monitoring_loop(interval)

if __name__ == "__main__":
    main()