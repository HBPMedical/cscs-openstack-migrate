# cscs-openstack-migrate

* Requires package python3-openstackclient
* Requires OpenStack YAML structured configuration, available on https://github.com/crochat/cscs-openstack-config

Check the parameters with:
./os_vm_transfer.py --help

Make sure than you configure your OpenStack client as mentioned in cscs-openstack-config repository.
You should be able to connect (and test) on both environments with:

```
openstack --os-cloud <POLLUX_PROJECT> flavor list
```

```
openstack --os-cloud <CASTOR_PROJECT> flavor list
```

Once these commands work like a charm, you're ready for the next step!

The default transfer command is

```
./os_vm_transfer.py --export-cloud <POLLUX_PROJECT> --import-cloud <CASTOR_PROJECT> --vm <VM>
```

It will:

* Export (on Pollux)
  * Get details (also the boot volume ID if it exists) from VM
  * Shutdown the VM
  * Create a volume snapshot (in case of boot volume) or a server snapshot
  * Create a new volume from the snapshot
  * Create an image from the snapshot
  * Save the image as a file
  * Compare the checksum of the saved image with the source image
* Import (on Castor)
  * Create an image from the file
  * Compare the checksum of the image with the source file
  * Create a boot volume from the image
  * Create the server from the boot volume, with the same subnet, IP address, name, flavor... that was on Pollux
  * If the machine HAD a floating IP on Pollux, it will do what it takes to get a NEW one on the VM on Castor. If a floating is available, it will connect it. Otherwise, it will first allocate a new floating to the project, then connect it.

As we use it for our own needs, maybe it doesn't precisely fits yours. Feel free to suggest modifications or to fork it, then propose a pull request.
We don't have multiple network interfaces per VM or multiple security groups (even if it should work). If you had the VM connected to a subnet with an IP on Pollux, it will connect it to the same subnet, with the same IP on Castor. Just make sure it exists prior to running the script.
