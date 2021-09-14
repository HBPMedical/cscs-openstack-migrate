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
./os_vm_transfer.py --os-export-cloud <POLLUX_PROJECT> --os-import-cloud <CASTOR_PROJECT> --vm <VM>
```

It will:

* Export (on Pollux)
  * Get details (also the boot volume ID if it exists) from VM on POLLUX
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
