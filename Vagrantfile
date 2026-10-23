
Vagrant.configure("2") do |config|

  config.vm.box = "ubuntu/jammy64"

  # Monitoring server
  config.vm.define "default" do |monitor|
    monitor.vm.hostname = "monitoring-lab"
    monitor.vm.network "private_network", ip: "192.168.56.10"

    monitor.vm.network "forwarded_port", guest: 8000, host: 8000,
      host_ip: "127.0.0.1", auto_correct: true
    monitor.vm.network "forwarded_port", guest: 9090, host: 9090,
      host_ip: "127.0.0.1", auto_correct: true
    monitor.vm.network "forwarded_port", guest: 3000, host: 3000,
      host_ip: "127.0.0.1", auto_correct: true

    monitor.vm.provider "virtualbox" do |vb|
      vb.name = "devops-monitoring-lab"
      vb.memory = 4096
      vb.cpus = 2
    end

    monitor.vm.provision "shell", inline: <<-SHELL
      set -eux
      apt-get update
      DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io docker-compose-v2 curl
      systemctl enable --now docker
    SHELL
  end

  # Linux server to monitor
  config.vm.define "linux-web-01" do |web|
    web.vm.hostname = "linux-web-01"
    web.vm.network "private_network", ip: "192.168.56.11"

    web.vm.provider "virtualbox" do |vb|
      vb.name = "linux-web-01"
      vb.memory = 1024
      vb.cpus = 1
    end
  end


  # Second Linux server to monitor
  config.vm.define "linux-web-02" do |web|
    web.vm.hostname = "linux-web-02"
    web.vm.network "private_network", ip: "192.168.56.12"

    web.vm.provider "virtualbox" do |vb|
      vb.name = "linux-web-02"
      vb.memory = 1024
      vb.cpus = 1
    end
  end

end
