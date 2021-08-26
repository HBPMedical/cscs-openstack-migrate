#!/usr/bin/env python3

image_format = 'qcow2'
polling_sleep_time = 10
polling_timeout = 600
default_min_ram = 2048
default_min_disk = 40

import os
import sys
import argparse
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--export-cloud', dest='export_cloud', type=str, help='Export cloud configuration name')
parser.add_argument('--import-cloud', dest='import_cloud', type=str, help='Import cloud configuration name')
parser.add_argument('--vm', dest='vm', type=str, help='VM name')
parser.add_argument('--volume-id', dest='volume_id', type=str, help='Volume ID')
parser.add_argument('--volume-snapshot-id', dest='snap_id', type=str, help='Volume snapshot ID')
parser.add_argument('--new-volume-id', dest='newvol_id', type=str, help='New volume ID (generated from volume snapshot)')
parser.add_argument('--image-id', dest='image_id', type=str, help='Image ID')
parser.add_argument('--image-filename', dest='image_filename', type=str, help='Image file path/filename')
parser.add_argument('--image-format', dest='image_format', type=str, help='Image format [default %s]' %(image_format))
parser.add_argument('--key-name', dest='key_name', type=str, help='Key name')
parser.add_argument('--security-group', dest='security_group', type=str, help='Security group')
parser.add_argument('--flavor-name', dest='flavor_name', type=str, help='Flavor name')
parser.add_argument('--subnet-name', dest='subnet_name', type=str, help='Subnet name')
parser.add_argument('--ip', dest='ip', type=str, help='VM IP address')
parser.add_argument('--min-ram', dest='min_ram', type=str, help='Min RAM (MiB) [default %s]' %(default_min_ram))
parser.add_argument('--min-disk', dest='min_disk', type=str, help='Min disk (GiB) [default %s]' %(default_min_disk))
parser.add_argument('--keep', action='store_true', help='Keep temporary items')
args = parser.parse_args()

class OSVM:
    __action = None
    __export_cloud = None
    __import_cloud = None
    __polling_sleep_time = None
    __polling_timeout = None
    __vm_name = None
    __volume_id = None
    __snap_id = None
    __snap_size = None
    __newvol_id = None
    __image_id = None
    __image_filename = None
    __image_file = None
    __image_format = None
    __key_name = None
    __security_group = None
    __flavor_name = None
    __subnet_name = None
    __ip = None
    __min_ram = None
    __min_disk = None
    __keep = False

    def __init__(self, export_cloud=None, import_cloud=None, vm_name=None, volume_id=None, snap_id=None, newvol_id=None, image_id=None, image_filename=None, key_name=None, security_group=None, flavor_name=None, subnet_name=None, ip=None, min_ram=None, min_disk=None, poll_sleep_time=None, poll_timeout=None):
        if export_cloud is not None and export_cloud != '':
            self.__export_cloud = export_cloud
        elif args.export_cloud is not None and args.export_cloud != '':
            self.__export_cloud = args.export_cloud

        if import_cloud is not None and import_cloud != '':
            self.__import_cloud = import_cloud
        elif args.import_cloud is not None and args.import_cloud != '':
            self.__import_cloud = args.import_cloud

        if vm_name is not None and vm_name != '':
            self.__vm_name = vm_name
        elif args.vm is not None and args.vm != '':
            self.__vm_name = args.vm

        if volume_id is not None and volume_id != '':
            self.__volume_id = volume_id
        elif args.volume_id is not None and args.volume_id != '':
            self.__volume_id = args.volume_id

        if snap_id is not None and snap_id != '':
            self.__snap_id = snap_id
        elif args.snap_id is not None and args.snap_id != '':
            self.__snap_id = args.snap_id

        if newvol_id is not None and newvol_id != '':
            self.__newvol_id = newvol_id
        elif args.newvol_id is not None and args.newvol_id != '':
            self.__newvol_id = args.newvol_id

        if image_id is not None and image_id != '':
            self.__image_id = image_id
        elif args.image_id is not None and args.image_id != '':
            self.__image_id = args.image_id

        if image_filename is not None and image_filename != '':
            self.__image_filename = image_filename
        elif args.image_filename is not None and args.image_filename != '':
            self.__image_filename = args.image_filename
        if self.__image_filename is not None and os.path.isfile(self.__image_filename):
            self.__image_file = self.__image_filename

        if args.image_format is not None and args.image_format != '':
            self.__image_format = args.image_format
        else:
            global image_format
            self.__image_format = image_format

        if key_name is not None and key_name != '':
            self.__key_name = key_name
        elif args.key_name is not None and args.key_name != '':
            self.__key_name = args.key_name

        if security_group is not None and security_group != '':
            self.__security_group = security_group
        elif args.security_group is not None and args.security_group != '':
            self.__security_group = args.security_group

        if flavor_name is not None and flavor_name != '':
            self.__flavor_name = flavor_name
        elif args.flavor_name is not None and args.flavor_name != '':
            self.__flavor_name = args.flavor_name

        if subnet_name is not None and subnet_name != '':
            self.__subnet_name = subnet_name
        elif args.subnet_name is not None and args.subnet_name != '':
            self.__subnet_name = args.subnet_name

        if ip is not None and ip != '':
            self.__ip = ip
        elif args.ip is not None and args.ip != '':
            self.__ip = args.ip

        if min_ram is not None and min_ram != '':
            self.__min_ram = min_ram
        elif args.min_ram is not None and args.min_ram != '':
            self.__min_ram = args.min_ram
        else:
            self.__min_ram = default_min_ram

        if min_disk is not None and min_disk != '':
            self.__min_disk = min_disk
        elif args.min_disk is not None and args.min_disk != '':
            self.__min_disk = args.min_disk
        else:
            self.__min_disk = default_min_disk

        if poll_sleep_time is not None and poll_sleep_time != '':
            self.__polling_sleep_time = poll_sleep_time
        else:
            global polling_sleep_time
            self.__polling_sleep_time = polling_sleep_time

        if poll_timeout is not None and poll_timeout != '':
            self.__polling_timeout = poll_timeout
        else:
            global polling_timeout
            self.__polling_timeout = polling_timeout

        if args.keep:
            self.__keep = True

        if self.__vm_name is not None:
            if self.__export_cloud is not None:
                if self.__import_cloud is not None:
                    self.__action = 'transfer'
                else:
                    self.__action = 'export'
            elif self.__import_cloud is not None and self.__key_name is not None and self.__flavor_name is not None and self.__subnet_name is not None:
                self.__action = 'import'

    def __get_os_cmd_result(self, cloud, cmd, return_col_name=None, filter_col_name=None, filter_col_val=None):
        result = None

        print('        openstack --os-cloud %s %s' %(cloud, cmd))
        proc = subprocess.run(['openstack --os-cloud %s %s' %(cloud, cmd)], shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        first_line = True
        return_col_id = None
        filter_col_id = None
        found = False
        for line in proc.stderr:
            raise Exception(line)

        for line in proc.stdout.splitlines():
            tmp_return_val = None
            #print(line)
            if line.startswith('+'):
                continue
            elif line.startswith('|'):
                fields = line.split('|')
                i = -1
                for field in fields:
                    field = field.strip()
                    if first_line:
                        if return_col_id is None and return_col_name is not None and field == return_col_name:
                            return_col_id = i
                        if filter_col_name is not None and filter_col_val is not None and filter_col_id is None:
                            if field == filter_col_name:
                                filter_col_id = i
                    else:
                        if return_col_id is not None and i == return_col_id:
                            tmp_return_val = field
                        if i == filter_col_id and field == filter_col_val:
                            found = True
                    i += 1
                if first_line:
                    first_line = False
                else:
                    if filter_col_id is not None and not found:
                        tmp_return_val = None

                    if tmp_return_val is not None:
                        if result is None:
                            result = ''
                        else:
                            result += '\n'

                        result += tmp_return_val

                    if filter_col_id is not None and found:
                        break
            elif first_line:
                raise Exception()

        return result

    def __poll(self, cloud, cmd, return_col_name, expected_result, filter_col_name, filter_col_val, timeout, polling_sleep_time=None):
        result = False

        while result is False:
            tmp_result = self.__get_os_cmd_result(cloud, cmd, return_col_name, filter_col_name, filter_col_val)
            if tmp_result is not None and tmp_result == expected_result:
                result = True
            elif expected_result is None and tmp_result is None:
                result = True
            else:
                if polling_sleep_time is None:
                    polling_sleep_time = self.__polling_sleep_time
                time.sleep(polling_sleep_time)

        return result

    def __is_vm_active(self, cloud, vm):
        result = False

        if self.__get_os_cmd_result(cloud, 'server show %s' %(vm), 'Value', 'Field', 'status') == 'ACTIVE':
            result = True

        return result

    def __vm_shutdown(self, cloud, vm):
        result = False

        res = self.__get_os_cmd_result(cloud, 'server stop %s' %(vm))
        print('    Waiting for server %s to stop...' %(vm))
        res = self.__poll(cloud, 'server show %s' %(vm), 'Value', 'SHUTOFF', 'Field', 'status', self.__polling_timeout)
        if result:
            result = True
            print('    Server %s stopped successfully.' %(vm))

        return result

    def __get_vm_info(self, cloud, vm):
        result = True

        if self.__volume_id is None:
            print('    Getting volume ID for server %s' %(vm))
            vol_id = None
            vol_id = self.__get_os_cmd_result(cloud, 'server show %s' %(vm), 'Value', 'Field', 'volumes_attached')
            vol_id = vol_id.split('=')[1].strip("'")
            if vol_id is not None and vol_id != '':
                self.__volume_id = vol_id
            else:
                result = False

        if result:
            print('    Volume ID: %s' %(self.__volume_id))
            if self.__key_name is None:
                key_name = None
                key_name = self.__get_os_cmd_result(cloud, 'server show %s' %(vm), 'Value', 'Field', 'key_name')
                if key_name is not None and key_name != '':
                    self.__key_name = key_name
                else:
                    result = False

        if result:
            print('    Key name: %s' %(self.__key_name))
            if self.__security_group is None:
                security_group = None
                security_group = self.__get_os_cmd_result(cloud, 'server show %s' %(vm), 'Value', 'Field', 'security_groups')
                security_group = security_group.split('=')[1].strip("'")
                if security_group is not None and security_group != '':
                    self.__security_group = security_group
                else:
                    result = False

        if result:
            print('    Security group: %s' %(self.__security_group))
            if self.__flavor_name is None:
                flavor_name = None
                flavor_name = self.__get_os_cmd_result(cloud, 'server show %s' %(vm), 'Value', 'Field', 'flavor')
                flavor_name = flavor_name.split()[0]
                if flavor_name is not None and flavor_name != '':
                    self.__flavor_name = flavor_name
                else:
                    result = False

        if result:
            print('    Flavor name: %s' %(self.__flavor_name))
            if self.__subnet_name is None or self.__ip is None:
                subnet_name = None
                ip = None
                addresses = self.__get_os_cmd_result(cloud, 'server show %s' %(vm), 'Value', 'Field', 'addresses')
                if self.__subnet_name is None:
                    subnet_name = addresses.split('=')[0]
                    if subnet_name is not None and subnet_name != '':
                        self.__subnet_name = subnet_name
                    else:
                        result = False
                if self.__ip is None:
                    ip = addresses.split('=')[1]
                    if ip is not None and ip != '':
                        self.__ip = ip
                    else:
                        result = False

        if result:
            print('    Subnet name: %s' %(self.__subnet_name))
            print('    IP: %s' %(self.__ip))

        return result

    def __create_snapshot(self, cloud, vm, volume_id):
        result = True

        print('    Creating volume snapshot %s.bkp from volume ID %s...' %(vm, volume_id))
        snap_id = None
        snap_id = self.__get_os_cmd_result(cloud, 'volume snapshot create --volume %s --force %s.bkp' %(volume_id, vm), 'Value', 'Field', 'id')
        if snap_id is not None and snap_id != '':
            print('    Volume snapshot ID: %s' %(snap_id))
            print('    Waiting for volume snapshot ID %s to be available...' %(snap_id))
            res = self.__poll(cloud, 'volume snapshot show %s' %(snap_id), 'Value', 'available', 'Field', 'status', self.__polling_timeout)
            if res:
                print('    Volume snapshot ID %s available.' %(snap_id))
                print('    Getting snapshot size for volume snapshot ID %s' %(snap_id))
                snap_size = None
                snap_size = self.__get_os_cmd_result(cloud, 'volume snapshot show %s' %(snap_id), 'Value', 'Field', 'size')
                if snap_size is not None and snap_size != '':
                    print('    Volume snapshot ID %s size: %s GB' %(snap_id, snap_size))
                else:
                    result = False
            else:
                result = False
        else:
            result = False

        if result:
            self.__snap_id = snap_id
            self.__snap_size = snap_size
            self.__min_disk = snap_size

        return result

    def __create_snapshot_volume(self, cloud, vm, snap_id, volume_size):
        result = True

        print('    Creating volume %s.bkp of size %s GB from volume snapshot ID %s...' %(vm, volume_size, snap_id))
        newvol_id = None
        newvol_id = self.__get_os_cmd_result(cloud, 'volume create --snapshot %s --size %s %s.bkp' %(snap_id, volume_size, vm), 'Value', 'Field', 'id')
        if newvol_id is not None and newvol_id != '':
            print('    Volume ID: %s' %(newvol_id))
            print('    Waiting for volume ID %s to be available...' %(newvol_id))
            res = self.__poll(cloud, 'volume show %s' %(newvol_id), 'Value', 'available', 'Field', 'status', self.__polling_timeout)
            if res:
                print('    Volume ID %s available.' %(newvol_id))
            else:
                result = False
        else:
            result = False

        if result:
            self.__newvol_id = newvol_id

        return result

    def __create_image(self, cloud, vm, newvol_id):
        result = True

        print('    Creating image %s.bkp from volume ID %s...' %(vm, newvol_id))
        image_id = None
        tries = 0
        while image_id is None and tries < 2:
            result = True
            image_id = None
            try:
                print('    - Try #%s...' %(tries))
                image_id = self.__get_os_cmd_result(cloud, 'image create --volume %s --unprotected --container-format bare --disk-format %s %s.bkp' %(newvol_id, self.__image_format, vm), 'Value', 'Field', 'image_id')
            except Exception as e:
                print(e)

            if image_id is not None and image_id != '':
                print('    Image ID: %s' %(image_id))
                print('    Waiting for image ID %s to be active...' %(image_id))

                res = False
                try:
                    res = self.__poll(cloud, 'image show %s' %(image_id), 'Value', 'active', 'Field', 'status', self.__polling_timeout)
                except Exception as e:
                    print(e)

                if res:
                    print('    Image ID %s available.' %(image_id))
                else:
                    result = False
                    image_id = None
            else:
                result = False
                image_id = None

            tries += 1

        if result:
            self.__image_id = image_id

        return result

    def __save_image(self, cloud, vm, image_id, filename=None):
        result = True

        if filename is None:
            filename = os.path.join('.', '%s.bkp.%s' %(vm, self.__image_format))

        print('    Saving image ID %s as file %s...' %(image_id, filename))
        tries = 0
        res = False
        while res is not None:
            try:
                print('    - Try #%s...' %(tries))
                res = False
                res = self.__get_os_cmd_result(cloud, 'image save --file %s %s' %(filename, image_id))
            except Exception as e:
                print(e)
            tries += 1

        if res is None:
            if os.path.exists(filename):
                print('    Image ID %s saved successfully and available as file %s.' %(image_id, filename))
            else:
                result = False
        else:
            result = False

        if result:
            self.__image_file = filename
        else:
            self.__image_file = None

        return result

    def __import_image(self, cloud, vm, image_file, image_format, min_ram, min_disk):
        result = True

        print('    Creating image %s.rst from image file %s...' %(vm, image_file))
        image_id = None
        tries = 0
        while image_id is None and tries < 2:
            result = True
            image_id = None
            try:
                print('    - Try #%s...' %(tries))
                image_id = self.__get_os_cmd_result(cloud, 'image create --file %s --container-format bare --disk-format %s --min-ram %s --min-disk %s %s.rst' %(image_file, image_format, min_ram, min_disk, vm), 'Value', 'Field', 'id')
            except Exception as e:
                print(e)

            if image_id is not None and image_id != '':
                print('    Image ID: %s' %(image_id))
                print('    Waiting for image ID %s to be active...' %(image_id))

                res = False
                try:
                    res = self.__poll(cloud, 'image show %s' %(image_id), 'Value', 'active', 'Field', 'status', self.__polling_timeout)
                except Exception as e:
                    print(e)

                if res:
                    print('    Image ID %s available.' %(image_id))
                else:
                    result = False
                    image_id = None
            else:
                result = False
                image_id = None

            tries += 1

        if result:
            self.__image_id = image_id

        return result

    def __create_image_volume(self, cloud, vm, image_id, volume_size):
        result = True

        print('    Creating bootable volume %s of size %s GB from image ID %s...' %(vm, volume_size, image_id))
        volume_id = None
        volume_id = self.__get_os_cmd_result(cloud, 'volume create --image %s --size %s --bootable %s' %(image_id, volume_size, vm), 'Value', 'Field', 'id')
        if volume_id is not None and volume_id != '':
            print('    Volume ID: %s' %(volume_id))
            print('    Waiting for volume ID %s to be available...' %(volume_id))
            res = self.__poll(cloud, 'volume show %s' %(volume_id), 'Value', 'available', 'Field', 'status', self.__polling_timeout)
            if res:
                print('    Volume ID %s available.' %(volume_id))
            else:
                result = False
        else:
            result = False

        if result:
            self.__volume_id = volume_id

        return result

    def __create_vm(self, cloud, vm, volume_id, key_name, security_group, flavor_name, subnet_name, ip=None):
        result = True

        print('    Creating VM %s from volume ID %s...' %(vm, volume_id))
        vm_id = None
        fixed_ip_opt = ''
        if ip is not None and ip != '':
            fixed_ip_opt = ',v4-fixed-ip=%s' %(ip)
        vm_id = self.__get_os_cmd_result(cloud, 'server create --flavor %s --volume %s --nic net-id=%s%s --security-group %s --key-name %s %s' %(flavor_name, volume_id, subnet_name, fixed_ip_opt, security_group, key_name, vm), 'Value', 'Field', 'id')
        if vm_id is not None and vm_id != '':
            print('    VM ID: %s' %(vm_id))
            print('    Waiting for VM ID %s to be available...' %(vm_id))
            res = self.__poll(cloud, 'server show %s' %(vm_id), 'Value', 'ACTIVE', 'Field', 'status', self.__polling_timeout)
            if res:
                print('    VM %s (ID %s) available.' %(vm, vm_id))
            else:
                result = False
        else:
            result = False

        return result

    def __clean_up(self, cloud, image_id=None, newvol_id=None, snap_id=None):
        result = True

        print('Cleaning up...')

        if image_id is not None:
            print('    Deleting image ID %s...' %(image_id))
            self.__get_os_cmd_result(cloud, 'image delete %s' %(image_id))
            res = self.__poll(cloud, 'image list', 'ID', None, 'ID', image_id, self.__polling_timeout)
            if res:
                print('    Image ID %s successfully deleted.' %(image_id))
            else:
                result = False

        if newvol_id is not None:
            print('    Deleting volume ID %s...' %(newvol_id))
            self.__get_os_cmd_result(cloud, 'volume delete %s' %(newvol_id))
            res = self.__poll(cloud, 'volume list', 'ID', None, 'ID', newvol_id, self.__polling_timeout)
            if res:
                print('    Volume ID %s successfully deleted.' %(newvol_id))
            else:
                result = False

        if snap_id is not None:
            print('    Deleting volume snapshot ID %s...' %(snap_id))
            self.__get_os_cmd_result(cloud, 'volume snapshot delete %s' %(snap_id))
            res = self.__poll(cloud, 'volume snapshot list', 'ID', None, 'ID', snap_id, self.__polling_timeout)
            if res:
                print('    Volume snapshot ID %s successfully deleted.' %(snap_id))
            else:
                result = False

        return result

    def __export(self):
        print('Preparing export of VM %s from cloud %s...' %(self.__vm_name, self.__export_cloud))
        # TODO:
        #   - name volumes as <VM>_boot in new servers
        #   - work also on servers without volumes: create image from server, save image, ...

        go_ahead = True

        if self.__image_file is None and self.__image_id is None and self.__newvol_id is None and self.__snap_id is None and self.__is_vm_active(self.__export_cloud, self.__vm_name):
            print('    Server %s is ACTIVE! Stopping it...' %(self.__vm_name))
            go_ahead = self.__vm_shutdown(self.__export_cloud, self.__vm_name)

        if go_ahead:
            if self.__action == 'export' and self.__volume_id is None:
                go_ahead = self.__get_vm_info(self.__export_cloud, self.__vm_name)
            elif self.__action == 'transfer' and self.__volume_id is None and self.__key_name is None and self.__security_group is None and self.__subnet_name is None:
                go_ahead = self.__get_vm_info(self.__export_cloud, self.__vm_name)

        if go_ahead and self.__image_file is None and self.__image_id is None and self.__newvol_id is None and self.__snap_id is None:
            go_ahead = self.__create_snapshot(self.__export_cloud, self.__vm_name, self.__volume_id)

        if go_ahead and self.__image_file is None and self.__image_id is None and self.__newvol_id is None:
            go_ahead = self.__create_snapshot_volume(self.__export_cloud, self.__vm_name, self.__snap_id, self.__snap_size)

        if go_ahead and self.__image_file is None and self.__image_id is None:
            go_ahead = self.__create_image(self.__export_cloud, self.__vm_name, self.__newvol_id)

        if go_ahead and self.__image_file is None:
            go_ahead = self.__save_image(self.__export_cloud, self.__vm_name, self.__image_id, self.__image_filename)

        if not self.__keep and (self.__image_id is not None or self.__newvol_id is not None or self.__snap_id is not None):
            go_ahead = self.__clean_up(self.__export_cloud, self.__image_id, self.__newvol_id, self.__snap_id)

    def __import(self):
        print('Preparing import of VM %s (file %s) in cloud %s...' %(self.__vm_name, self.__image_file, self.__import_cloud))

        go_ahead = True

        if self.__image_file is not None and self.__image_format is not None and self.__min_ram is not None and self.__min_disk is not None and self.__vm_name is not None and self.__image_id is None:
            go_ahead = self.__import_image(self.__import_cloud, self.__vm_name, self.__image_file, self.__image_format, self.__min_ram, self.__min_disk)

        if self.__vm_name is not None and self.__min_disk is not None and self.__image_id is not None and self.__volume_id is None:
            go_ahead = self.__create_image_volume(self.__import_cloud, self.__vm_name, self.__image_id, self.__min_disk)

        if self.__vm_name is not None and self.__volume_id is not None and self.__key_name is not None and self.__security_group is not None and self.__flavor_name is not None and self.__subnet_name is not None:
            go_ahead = self.__create_vm(self.__import_cloud, self.__vm_name, self.__volume_id, self.__key_name, self.__security_group, self.__flavor_name, self.__subnet_name, self.__ip)

        if not self.__keep and self.__image_id is not None:
            go_ahead = self.__clean_up(self.__import_cloud, self.__image_id)

    def run(self):
        if self.__action is not None:
            if self.__action == 'export':
                self.__export()
            elif self.__action == 'import':
                self.__import()
            elif self.__action == 'transfer':
                self.__export()

                self.__volume_id = None
                self.__snap_id = None
                self.__newvol_id = None
                self.__image_id = None

                self.__import()
        else:
            sys.exit('No action can be done!')

def main():
    osvm = OSVM()
    osvm.run()

if __name__ == '__main__':
    main()
