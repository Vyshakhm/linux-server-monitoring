from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import psutil
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

# The container mounts the VM's /proc at /host/proc and runs in the host PID
# namespace, allowing psutil to read VM-wide CPU, memory, and process metrics.
psutil.PROCFS_PATH = os.getenv("HOST_PROC", "/proc")

registry = CollectorRegistry()
cpu_percent = Gauge("system_cpu_usage_percent", "CPU usage percentage for the Linux VM", registry=registry)
memory_total = Gauge("system_memory_total_bytes", "Total memory bytes on the Linux VM", registry=registry)
memory_available = Gauge("system_memory_available_bytes", "Available memory bytes on the Linux VM", registry=registry)
disk_total = Gauge("system_disk_total_bytes", "Total bytes on the Linux VM root filesystem", registry=registry)
disk_free = Gauge("system_disk_free_bytes", "Free bytes on the Linux VM root filesystem", registry=registry)
process_count = Gauge("system_process_count", "Number of processes on the Linux VM", registry=registry)


def collect_metrics():
    cpu_percent.set(psutil.cpu_percent(interval=0.2))
    mem = psutil.virtual_memory()
    memory_total.set(mem.total)
    memory_available.set(mem.available)
    # /host/root is a read-only bind mount of the VM's root filesystem.
    disk = psutil.disk_usage("/host/root")
    disk_total.set(disk.total)
    disk_free.set(disk.free)
    process_count.set(len(psutil.pids()))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        if self.path == "/metrics":
            collect_metrics()
            body = generate_latest(registry)
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404, "Use /health or /metrics")

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    host = os.getenv("EXPORTER_HOST", "0.0.0.0")
    port = int(os.getenv("EXPORTER_PORT", "8000"))
    print(f"Starting VM metrics exporter on {host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()
