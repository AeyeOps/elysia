#!/usr/bin/env python3
"""
resource_monitoring.py - Track system resources during tests
"""

import sys
import os
import time
import psutil
import threading
import json
import subprocess
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

import time
time.sleep(60)

from dotenv import load_dotenv

def get_docker_stats():
    """Get Docker container resource usage"""
    try:
        # Get stats for all phase4 containers
        containers = ["test-node1", "test-node2", "test-node3"]
        stats = {}

        for container in containers:
            try:
                # Get Docker stats
                result = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format", "json", container],
                    capture_output=True, text=True, timeout=10
                )

                if result.returncode == 0:
                    stat_data = json.loads(result.stdout.strip())
                    stats[container] = {
                        'cpu_percent': float(stat_data.get('CPUPerc', '0%').rstrip('%')),
                        'memory_usage': stat_data.get('MemUsage', '0B/0B'),
                        'memory_percent': float(stat_data.get('MemPerc', '0%').rstrip('%')),
                        'net_io': stat_data.get('NetIO', '0B/0B'),
                        'block_io': stat_data.get('BlockIO', '0B/0B'),
                        'container': stat_data.get('Container', container)
                    }
                else:
                    stats[container] = {'error': 'Container not found or not running'}

            except Exception as e:
                stats[container] = {'error': str(e)}

        return stats

    except Exception as e:
        return {'error': str(e)}

def get_system_stats():
    """Get overall system resource usage"""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv,
                'packets_sent': psutil.net_io_counters().packets_sent,
                'packets_recv': psutil.net_io_counters().packets_recv
            }
        }
    except Exception as e:
        return {'error': str(e)}

def monitor_resources(duration_seconds=60, interval_seconds=5):
    """Monitor resources for a specified duration"""
    print(f"📊 MONITORING RESOURCES for {duration_seconds} seconds")
    print("=" * 60)

    monitoring_data = {
        'start_time': time.time(),
        'duration': duration_seconds,
        'interval': interval_seconds,
        'system_stats': [],
        'docker_stats': []
    }

    end_time = time.time() + duration_seconds
    sample_count = 0

    print("   Recording resource usage... (Ctrl+C to stop early)")

    try:
        while time.time() < end_time:
            sample_time = time.time()
            sample_count += 1

            # Collect system stats
            sys_stats = get_system_stats()
            sys_stats['timestamp'] = sample_time
            sys_stats['sample'] = sample_count
            monitoring_data['system_stats'].append(sys_stats)

            # Collect Docker stats
            docker_stats = get_docker_stats()
            docker_stats['timestamp'] = sample_time
            docker_stats['sample'] = sample_count
            monitoring_data['docker_stats'].append(docker_stats)

            print(f"   📊 Sample {sample_count}: CPU {sys_stats.get('cpu_percent', 'N/A')}%, "
                  f"Mem {sys_stats.get('memory', {}).get('percent', 'N/A')}%")

            # Wait for next interval
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("   ⏹️  Monitoring stopped by user")
        monitoring_data['duration'] = time.time() - monitoring_data['start_time']

    monitoring_data['end_time'] = time.time()
    monitoring_data['actual_duration'] = monitoring_data['end_time'] - monitoring_data['start_time']
    monitoring_data['total_samples'] = sample_count

    return monitoring_data

def analyze_resource_usage(monitoring_data):
    """Analyze collected resource usage data"""
    if not monitoring_data or 'system_stats' not in monitoring_data:
        return None

    print("\n" + "=" * 70)
    print("📊 RESOURCE USAGE ANALYSIS")
    print("=" * 70)

    analysis = {
        'summary': {},
        'system': {},
        'docker': {},
        'recommendations': []
    }

    # Analyze system stats
    system_stats = monitoring_data['system_stats']
    if system_stats:
        cpu_percents = [s.get('cpu_percent', 0) for s in system_stats if isinstance(s.get('cpu_percent'), (int, float))]
        memory_percents = [s.get('memory', {}).get('percent', 0) for s in system_stats if isinstance(s.get('memory', {}).get('percent'), (int, float))]

        analysis['system'] = {
            'cpu_avg': sum(cpu_percents) / len(cpu_percents) if cpu_percents else 0,
            'cpu_max': max(cpu_percents) if cpu_percents else 0,
            'cpu_min': min(cpu_percents) if cpu_percents else 0,
            'memory_avg': sum(memory_percents) / len(memory_percents) if memory_percents else 0,
            'memory_max': max(memory_percents) if memory_percents else 0,
            'memory_min': min(memory_percents) if memory_percents else 0,
            'samples': len(system_stats)
        }

        print(f"""
🖥️  SYSTEM RESOURCE USAGE:
   CPU: Avg {analysis['system']['cpu_avg']:.1f}%, Max {analysis['system']['cpu_max']:.1f}%, Min {analysis['system']['cpu_min']:.1f}%
   Memory: Avg {analysis['system']['memory_avg']:.1f}%, Max {analysis['system']['memory_max']:.1f}%, Min {analysis['system']['memory_min']:.1f}%
""")

    # Analyze Docker container stats
    docker_stats = monitoring_data['docker_stats']
    if docker_stats:
        container_analysis = {}

        for sample in docker_stats:
            for container_name, stats in sample.items():
                if container_name in ['timestamp', 'sample']:
                    continue

                if container_name not in container_analysis:
                    container_analysis[container_name] = {
                        'cpu_percents': [],
                        'memory_percents': []
                    }

                if isinstance(stats, dict) and 'cpu_percent' in stats:
                    container_analysis[container_name]['cpu_percents'].append(stats['cpu_percent'])
                if isinstance(stats, dict) and 'memory_percent' in stats:
                    container_analysis[container_name]['memory_percents'].append(stats['memory_percent'])

        analysis['docker'] = {}
        print("""
🐳 DOCKER CONTAINER USAGE:""")
        for container, data in container_analysis.items():
            cpu_avg = sum(data['cpu_percents']) / len(data['cpu_percents']) if data['cpu_percents'] else 0
            cpu_max = max(data['cpu_percents']) if data['cpu_percents'] else 0
            mem_avg = sum(data['memory_percents']) / len(data['memory_percents']) if data['memory_percents'] else 0
            mem_max = max(data['memory_percents']) if data['memory_percents'] else 0

            analysis['docker'][container] = {
                'cpu_avg': cpu_avg,
                'cpu_max': cpu_max,
                'memory_avg': mem_avg,
                'memory_max': mem_max
            }

            print(f"""   {container}:
     CPU: Avg {cpu_avg:.1f}%, Max {cpu_max:.1f}%
     Memory: Avg {mem_avg:.1f}%, Max {mem_max:.1f}%
""")

    # Generate recommendations
    recommendations = []

    if analysis['system'].get('cpu_avg', 0) > 80:
        recommendations.append("⚠️  High CPU usage detected - consider scaling resources")
    elif analysis['system'].get('cpu_avg', 0) > 50:
        recommendations.append("ℹ️  Moderate CPU usage - monitor during peak loads")

    if analysis['system'].get('memory_avg', 0) > 80:
        recommendations.append("⚠️  High memory usage detected - consider increasing memory allocation")
    elif analysis['system'].get('memory_avg', 0) > 60:
        recommendations.append("ℹ️  Moderate memory usage - monitor for memory leaks")

    for container, stats in analysis['docker'].items():
        if stats.get('cpu_avg', 0) > 70:
            recommendations.append(f"⚠️  Container {container} has high CPU usage")
        if stats.get('memory_avg', 0) > 70:
            recommendations.append(f"⚠️  Container {container} has high memory usage")

    if not recommendations:
        recommendations.append("✅ Resource usage is within acceptable limits")

    analysis['recommendations'] = recommendations

    print("""
💡 RECOMMENDATIONS:""")
    for rec in recommendations:
        print(f"   {rec}")

    # Overall assessment
    cpu_acceptable = analysis['system'].get('cpu_avg', 0) <= 70
    memory_acceptable = analysis['system'].get('memory_avg', 0) <= 70

    success = cpu_acceptable and memory_acceptable

    if success:
        print("\n🎉 RESOURCE MONITORING COMPLETE")
        print("   ✅ Resource usage is within acceptable limits")
        print("   📊 System is performing efficiently")
    else:
        print("\n⚠️  RESOURCE MONITORING COMPLETE WITH ISSUES")
        print("   ❌ Resource usage exceeds recommended limits")
        print("   📊 Consider resource optimization or scaling")

    return analysis

def run_load_test_with_monitoring(test_duration=120):
    """Run a load test while monitoring resources"""
    print("🔥 RUNNING LOAD TEST WITH RESOURCE MONITORING")
    print("=" * 60)

    # Start resource monitoring in a separate thread
    monitoring_data = {'monitoring_active': False}

    def monitoring_thread():
        monitoring_data.update(monitor_resources(duration_seconds=test_duration, interval_seconds=10))
        monitoring_data['monitoring_active'] = True

    monitor_thread = threading.Thread(target=monitoring_thread, daemon=True)
    monitor_thread.start()

    # Run a simple load test (you can replace this with actual test logic)
    print("   🧪 Running load test...")

    # Simulate some load by creating connections and operations
    try:
        import weaviate
        import urllib.request

        # Connect to cluster and perform operations
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        # Perform various operations to generate load
        operations_count = 0

        for i in range(50):  # Adjust based on desired load
            try:
                # Simple query operation
                collections = client.collections.list_all()
                operations_count += 1

                # Brief pause
                time.sleep(0.1)

            except Exception as e:
                print(f"   ⚠️  Load test operation {i} failed: {e}")

        client.close()

        print(f"   ✅ Completed {operations_count} operations during load test")

    except Exception as e:
        print(f"   ❌ Load test failed: {e}")

    # Wait for monitoring to complete
    print("   ⏳ Waiting for resource monitoring to complete...")
    monitor_thread.join(timeout=30)

    if monitoring_data.get('monitoring_active'):
        return monitoring_data
    else:
        print("   ⚠️  Resource monitoring did not complete properly")
        return None

def main():
    """Main function for resource monitoring"""
    print("🚀 STARTING RESOURCE MONITORING")
    print("   Tracking CPU/memory usage during operations")
    print("=" * 70)

    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Check Docker availability
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, timeout=10)
        docker_available = result.returncode == 0
    except:
        docker_available = False

    if not docker_available:
        print("⚠️  WARNING: Docker not available - container stats will not be collected")

    # Option 1: Simple resource monitoring
    print("\n🔹 OPTION 1: BASIC RESOURCE MONITORING")
    basic_monitoring = monitor_resources(duration_seconds=30, interval_seconds=5)

    if basic_monitoring:
        analysis = analyze_resource_usage(basic_monitoring)

        # Save basic monitoring results
        results_file = os.path.join(os.path.dirname(__file__), 'resource_monitoring_basic.json')
        with open(results_file, 'w') as f:
            json.dump(basic_monitoring, f, indent=2, default=str)

        print(f"\n💾 Basic monitoring results saved to: resource_monitoring_basic.json")

    # Option 2: Load test with monitoring
    print("\n🔹 OPTION 2: LOAD TEST WITH MONITORING")
    load_monitoring = run_load_test_with_monitoring(test_duration=60)

    if load_monitoring:
        analysis = analyze_resource_usage(load_monitoring)

        # Save load test results
        results_file = os.path.join(os.path.dirname(__file__), 'resource_monitoring_load.json')
        with open(results_file, 'w') as f:
            json.dump(load_monitoring, f, indent=2, default=str)

        print(f"\n💾 Load test results saved to: resource_monitoring_load.json")
        print("\n🎉 RESOURCE MONITORING COMPLETE")
        print("   📊 Resource usage data collected and analyzed")
        print("   💾 Results saved to JSON files for further analysis")
        return True

    else:
        print("\n⚠️  RESOURCE MONITORING COMPLETED WITH ISSUES")
        print("   ❌ Some monitoring operations failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)