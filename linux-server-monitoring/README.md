# Multi-Server Linux Monitoring Lab

A hands-on monitoring lab built with **Vagrant**, **VirtualBox**,
**Prometheus**, **Grafana**, and **Prometheus Node Exporter**. It
monitors two Ubuntu Linux servers and displays CPU, memory, disk, and
process metrics in Grafana.

## Architecture

``` text
Windows host
└── VirtualBox / Vagrant private network (192.168.56.0/24)
    ├── monitoring-lab  (192.168.56.10)
    │   ├── Python exporter :8000
    │   ├── Prometheus      :9090
    │   └── Grafana         :3000
    ├── linux-web-01        (192.168.56.11)
    │   └── Node Exporter   :9100
    └── linux-web-02        (192.168.56.12)
        └── Node Exporter   :9100
```

Prometheus scrapes the Python exporter and both Linux servers every 15
seconds.

## Components

  -------------------------------------------------------------------------
  Component               Purpose                 Address / port
  ----------------------- ----------------------- -------------------------
  `monitoring-lab`        Monitoring VM hosting   `192.168.56.10`
                          Docker Compose services 

  Python exporter         Custom metrics exporter `http://localhost:8000`

  Prometheus              Scrapes and stores      `http://localhost:9090`
                          time-series metrics     

  Grafana                 Dashboards and          `http://localhost:3000`
                          visualization           

  `linux-web-01`          First monitored Linux   `192.168.56.11`
                          server                  

  `linux-web-02`          Second monitored Linux  `192.168.56.12`
                          server                  

  Node Exporter           Exposes Linux host      Port `9100` on each
                          metrics                 server
  -------------------------------------------------------------------------

## Prerequisites

-   Windows host with VirtualBox and Vagrant installed.
-   Vagrant project directory containing the `Vagrantfile`.
-   Project shared into the monitoring VM at `/vagrant`.
-   Docker and Docker Compose available on `monitoring-lab`.
-   Network connectivity between VMs on the private network.

## Project layout

The monitoring project is located in the monitoring VM at
`/vagrant/linux-server-monitoring/`:

``` text
linux-server-monitoring/
├── app/
├── grafana/
├── prometheus/
│   ├── prometheus.yml
│   └── alert_rules.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

The Windows Vagrant project used in this lab is:

``` text
C:\Users\VYSHAKH\Desktop\vagrant\Ubuntu_Linux_monitoring
```

Adjust this path if your project is stored elsewhere.

## Start the lab

Open PowerShell on Windows:

``` powershell
cd C:\Users\VYSHAKH\Desktop\vagrant\Ubuntu_Linux_monitoring
```

Start the VMs:

``` powershell
vagrant up default
vagrant up linux-web-01
vagrant up linux-web-02
vagrant status
```

Expected private IP addresses:

-   Monitoring VM: `192.168.56.10`
-   First monitored server: `192.168.56.11`
-   Second monitored server: `192.168.56.12`

Optional connectivity checks from Windows:

``` powershell
ping 192.168.56.10
ping 192.168.56.11
ping 192.168.56.12
```

## Install Node Exporter

Run the following on **each monitored server**. Connect from PowerShell
with `vagrant ssh linux-web-01` or `vagrant ssh linux-web-02`:

``` bash
sudo apt-get update
sudo apt-get install -y prometheus-node-exporter
sudo systemctl status prometheus-node-exporter --no-pager
curl -s http://localhost:9100/metrics | head
```

The service should show `active (running)`, and the metrics endpoint
should return lines beginning with `# HELP` and `# TYPE`.

## Configure Prometheus

Edit `/vagrant/linux-server-monitoring/prometheus/prometheus.yml`.
Preserve the existing `global` and `rule_files` sections, and ensure
`scrape_configs` includes all three jobs:

``` yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/alert_rules.yml

scrape_configs:
  - job_name: python-exporter
    static_configs:
      - targets: ["exporter:8000"]

  - job_name: linux-servers
    static_configs:
      - targets: ["192.168.56.11:9100"]
        labels:
          instance: linux-web-01

  - job_name: linux-servers-2
    static_configs:
      - targets: ["192.168.56.12:9100"]
        labels:
          instance: linux-web-02
```

### Validate the configuration

Run on `monitoring-lab`:

``` bash
cd /vagrant/linux-server-monitoring
sudo docker compose run --rm --no-deps \
  --entrypoint=/bin/promtool \
  prometheus check config /etc/prometheus/prometheus.yml
```

The output should confirm that the Prometheus configuration is valid and
that alert rules were found.

### Apply the configuration

``` bash
sudo docker compose up -d --force-recreate prometheus
sudo docker compose ps
```

Test reachability from `monitoring-lab`:

``` bash
curl -s http://192.168.56.11:9100/metrics | head
curl -s http://192.168.56.12:9100/metrics | head
```

## Open the web interfaces

From the Windows host:

-   Prometheus targets: http://localhost:9090/targets
-   Prometheus query page: http://localhost:9090/graph
-   Grafana: http://localhost:3000

On the Prometheus Targets page, confirm these targets are `UP`:

-   `exporter:8000` under `python-exporter`
-   `192.168.56.11:9100` under `linux-servers`
-   `192.168.56.12:9100` under `linux-servers-2`

## Grafana dashboard

Open Grafana and select **Infrastructure → Linux Server Health**. The
dashboard panels should use queries that select both Linux server jobs.

### CPU usage (%)

``` promql
100 * (1 - avg by (instance) (
  rate(node_cpu_seconds_total{job=~"linux-servers|linux-servers-2", mode="idle"}[5m])
))
```

### Available memory (bytes)

``` promql
node_memory_MemAvailable_bytes{job=~"linux-servers|linux-servers-2"}
```

### Available disk space on root filesystem (bytes)

``` promql
node_filesystem_avail_bytes{
  job=~"linux-servers|linux-servers-2",
  mountpoint="/",
  fstype!~"tmpfs|overlay|squashfs"
}
```

### Running or runnable process count

``` promql
node_procs_running{job=~"linux-servers|linux-servers-2"}
```

After editing a panel, click **Run queries**, confirm both server series
appear, click **Apply**, and save the dashboard.

Note: `node_procs_running` counts processes in a running or runnable
state; it is not the total process count.

## Troubleshooting

### Docker permission denied

If Docker reports permission denied for `/var/run/docker.sock`, run
Docker Compose commands with `sudo`, for example:

``` bash
sudo docker compose ps
```

### New targets do not appear in Prometheus

First inspect the file on disk:

``` bash
cat /vagrant/linux-server-monitoring/prometheus/prometheus.yml
```

Then inspect the configuration loaded by the running container:

``` bash
sudo docker exec linux-monitor-prometheus cat /etc/prometheus/prometheus.yml
```

If the on-disk file is correct but the container has an older
configuration, recreate Prometheus:

``` bash
cd /vagrant/linux-server-monitoring
sudo docker compose up -d --force-recreate prometheus
```

### Node Exporter is not running

On the affected server:

``` bash
sudo systemctl status prometheus-node-exporter --no-pager
sudo systemctl restart prometheus-node-exporter
curl -s http://localhost:9100/metrics | head
```

### Target is DOWN

From `monitoring-lab`, test each server:

``` bash
curl -s http://192.168.56.11:9100/metrics | head
curl -s http://192.168.56.12:9100/metrics | head
```

Confirm the VM is running and the configured IP address is correct.

## Security notes

-   This lab's Compose configuration uses initial Grafana credentials
    `admin` / `admin`. Change the password before using the lab beyond
    local testing.
-   Restrict monitoring ports to trusted networks. Do not expose
    Prometheus, Grafana, or Node Exporter directly to the public
    internet.
-   Adjust IP addresses and port mappings if your Vagrantfile or Compose
    configuration differs.

## Current lab checklist

-   [x] Vagrant VMs created and reachable.
-   [x] Node Exporter running on `linux-web-01`.
-   [x] Node Exporter running on `linux-web-02`.
-   [x] Prometheus scraping both Linux servers.
-   [x] Prometheus targets verified as `UP`.
-   [x] Grafana CPU, memory, disk, and process panels configured for
    both servers.

## Possible next improvements

-   Add alerts for unreachable servers, high CPU usage, and low disk
    space.
-   Provision Node Exporter automatically using Vagrant.
-   Add server-specific dashboard variables and clearer units.
-   Configure alert delivery to email or a messaging platform.
