# Pull-Request-Metrics

![pylint](https://img.shields.io/badge/pylint-9.57-green?logo=python&logoColor=white)

The Pull Request Metrics tool will be used to gather data around the team's pull requests in a selected group of repositories associated with the Cloud Team. Core metrics include Average Time to First Review (Velocity), Average Line Count in PRs per repository (Complexity) and Total PR count (Volume). This should give us insights to where we can improve our code reviews, identify complex or difficult to review repositories and which ones need some extra care and attention, all in the name of improving team efficiency.

The final outcome are the mentioned metrics that can be visualised using Grafana and analysed to map out trends. 

## Deployment

Prerequisites:

    1. Ubuntu l3.nano or l3.micro VM (for the ansible controller)
    2. Additional 3 Ubuntu VMs (any l3 VM will do, 1 for the exporter, 1 for prometheus and 1 for Grafana)


To start deploying the stack, you will need a Ubuntu VM (`l3.nano` or `l3.micro` will do) with Ansible and Ansible-Core installed. It is recommended to install the latest version as some modules in the `deploy.yml` playbook are not supported in older versions. As of writing this, the current versions were used and installed via pip:

```
pip install ansible==10.7.0

pip install ansible-core==2.17.14
```


When SSHing onto the VM, make sure to add the `-A` flag to enable authentication agent forwarding, Ansible will need this to connect to the hosts. Next clone the Pull-Request-Metrics repo onto the VM, https://github.com/Dmitry-Popovichev/Pull-Request-Metrics.


### File editing and Setup

Using whatever terminal editor you have, edit the `hosts` file in either the dev or prod directories and specify the host IP for each group (exporter, Prometheus, Grafana), it will look something like this:

```yaml
---
[prometheus]
172.16.x.x1

[exporter]
172.16.x.x2

[grafana]
172.16.x.x3
```


By default, without specifying a hosts file when deploying, the deploy playbook will run the setup on the dev environment (using `ansible/dev/hosts`) as this avoids pushing the service straight into a production environment. You can change this by adding the following `-i path/to/the/production/hosts/file` to the deploy command in a later step or by changing the default hosts file in the `ansible.cfg` file.

Additionally, you will need to edit the `../group_vars/all.yml` file and specify the exporter host IP. This file exists for both dev and prod, therefore make sure to change either or both files depending on where you are deploying to. Don't change the `exporter_port` unless you also change it in the `main.py` script in the source code directory.

```yaml
---
exporter_host: "172.16.x.x"
exporter_port: "8081"
```


### Handling secrets and passwords

A `secrets.yml` file is included in the repository, this contains the GitHub Personal Access Token (PAT) that is used to contact the GitHub API and pull the metrics. It is encrypted using Ansible Vault and therefore you will need to access the Keeper record with the password in order to run the deployment or rotate the PAT if it has expired. The record is called `Pull Request Metrics - Ansible Vault`.

`CD` into the ansible directory and create a .vault_pass file in the Ansible Controller VM and add the password from the Keeper record. This will allow you to run the deployment command without using the `--ask-vault-password` flag and having to enter the password each time.

```bash
cd Pull-Request-Metrics/ansible

vim .vault_pass
```


>[!WARNING] Do not commit the `.vault_pass` file to the repository if making changes. It is ignored in the `.gitignore` file so make sure to spell the name correctly.


IMPORTANT NOTE: You might need to use your own GitHub PAT as the one in the secrets.yml file is associated with my personal account.

In your Ansible Controller VM, `cd` into the correct directory and use the ansible vault commands to edit the `secrets.yml` and add your own PAT. Use the Keeper record password to pass authentication.

```bash
cd Pull-Request-Metrics/ansible

ansible-vault edit secrets.yml
```


### Deployment

It is recommended to setup up the persistent storage on the Prometheus VM before running deployment to avoid any errors and having to restart services. To do so follow the instruction on setting up storage in the section below.

> Additional Note: make sure you have setup the security groups for each VM. By default Grafana is run on port 3000, Prometheus is run on port 9090 and port 8081 has been chosen for the exporter.


Run deployment:

```bash
cd Pull-Request-Metrics/ansible

# Run this with -v or -vvv to run it in verbose mode for troubleshooting
ansible-playbook deploy.yml

# or

ansible-playbook deploy.yml --ask-vault-password # if not using a .vault_password file.
```

The final step would be to set up your Grafana data sources and create some dashboards with metric visulisations.


## Custom repository list

By default, the stack runs across a number of repositories listed in the `vars.py` file which can be found under the `src/` directory. You can edit this file using any terminal editor and add your own repositories to see current metrics.

Because we are using Prometheus for the time being, we cannot backdate any of the data and therefore you won't see any trends until it has been running for a few weeks or months, but you will see the statisitics calculated as of the current date.

If you have already deployed the stack, please make sure to redeploy the `exporter` role as this applies the changes to the to the docker image and rebuilds the container.

```bash
ansible-playbook deploy.yml -t exporter

#or

ansible-playbook deploy.yml --ask-vault-password -t exporter # if not using a .vault_password file.
```


## Persistent Storage Configuration

If using a persistent storage such as a cinder volume to store the Prometheus scrape data, there are a few steps that need to be taken to format the volume, mount it and update the file systems table to ensure it is truly persistent.


### Step 1: Creating and attaching a volume

Make sure your instance has a volume attached to it, this can be down using the Horizon Web UI or via the command line.

A guide to how to do this can be found in the OpenStack docs following this link https://docs.openstack.org/horizon/latest/user/manage-volumes.html


### Step 2: Formatting the volume

Once attached to your VM, you can run `lsblk` within your VM instance terminal to see what device name the disk has been given. Typically, they will follow on chronologically/alphabetically, so your root device may be called `/dev/sda` and therefore the next one along would be called `/dev/sdb`.

Next, we need to format the raw block device and initialise the filesystem:

```
sudo mkfs.ext4 /dev/<device_name>
```


> [!WARNING] Data Destructive Action: This process is "destructive." Running this command will overwrite any existing data and the partition table on the target device. Always verify the device identifier (e.g., /dev/sdb vs /dev/sdc) using `lsblk` before proceeding.


### Step 3: Making the data directory and mounting the device

Run the next command to make a directory in the `/mnt/` directory where you want to store your data and set the permissions to the prometheus user (very important):

```
sudo mkdir /mnt/<name_of_data_dir>
```

```
sudo chown -R prometheus:prometheus /mnt/<name_of_data_dir>
```


Then mount your device to that directory:

```
sudo mount /dev/<device_name> /mnt/<name_of_data_dir>
```


### Step 4: Configuring persistent mounts

This last step is to update the file systems table to ensure that the storage mount doesn't disappear in the case of a VM reboot or if the power cycles. This is done by mounting using a UUID rather than the device name and updating the order which the OS reads this disk, this ensures the OS mounts from the correct disk in case of a hardware change.

First you will need the disk UUID, run the command below and look for the UUID field next to your device name:

```
blkid
```


Next edit the file systems table located in `/etc/fstab` and add a new line with the following:

```
UUID=<UUID> <mount_point> <file_system_type> <options> <dump> <pass>
```


It will look something like this with 0 meaning "Ignore this partition during backups" and 2 "Check this after the root partition is finished.":

```
UUID:3333ff9a-4aa4-4bbb-8ddd-4444ff1a1d1a /mnt/data/metrics/ ext4 defaults,nofail 0 2
```


> Save your file and you should be ready to go. Remember to edit your `prometheus.service` file to write the data to the new `/mnt/<name_of_data_dir>` location using the ` --storage.tsdb.path=` flag.
