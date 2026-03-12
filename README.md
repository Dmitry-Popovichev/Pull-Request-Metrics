# Pull-Request-Metrics

![pylint](https://img.shields.io/badge/pylint-8.82-yellowgreen?logo=python&logoColor=white)

The Pull Request Metrics tool will be used to gather data around the team's pull requests in a selected group of repositories associated with the Cloud Team. This should give us insights to where we can improve our code reviews, which repositories need some extra care and attention, and improve efficiency.

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

Run the next command to make a directory in the `/mnt/` directory, where you want to store your data:

```
sudo mkdir /mnt/<name_of_data_dir>
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