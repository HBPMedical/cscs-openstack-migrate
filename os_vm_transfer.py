#!/usr/bin/env python3

image_format = 'qcow2'
polling_sleep_time = 10
polling_timeout = 600
default_min_ram = 2048
default_min_disk = 40
external_network = 'ext-net1'

import os
import sys
import argparse
import subprocess
import json
import time
from datetime import timezone
import datetime
import hashlib

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
parser.add_argument('--security-groups', dest='security_groups', type=str, help='Security groups (comma-separated)')
parser.add_argument('--flavor-name', dest='flavor_name', type=str, help='Flavor name')
parser.add_argument('--size', dest='vm_size', type=str, help='VM size (GiB)')
parser.add_argument('--subnet-names', dest='subnet_names', type=str, help='Subnet names (comma-separated)')
parser.add_argument('--ips', dest='ips', type=str, help='VM IP addresses (comma-separated, must match subnet-names in the same order)')
parser.add_argument('--min-ram', dest='min_ram', type=str, help='Min RAM (MiB) [default %s]' %(default_min_ram))
parser.add_argument('--min-disk', dest='min_disk', type=str, help='Min disk (GiB) [default %s]' %(default_min_disk))
parser.add_argument('--keep', action='store_true', help='Keep temporary items')
parser.add_argument('--verbose-level', dest='verbose_level', type=int, help='Verbose level [default 1]')
args = parser.parse_args()

verbose_level = 1
if args.verbose_level is not None:
    verbose_level = args.verbose_level

class OSVM:
    __action = None
    __export_cloud = None
    __import_cloud = None
    __polling_sleep_time = None
    __polling_timeout = None
    __vm_name = None
    __volume_id = None
    __snap_id = None
    __vm_id = None
    __vm_size = None
    __newvol_id = None
    __image_id = None
    __image_filename = None
    __image_file = None
    __image_format = None
    __image_checksum = None
    __image_file_checksum = None
    __export_checksum_ok = False
    __import_checksum_ok = False
    __key_name = None
    __security_groups = None
    __flavor_name = None
    __subnet_names = None
    __ips = None
    __has_floating = False
    __floating_subnet = None
    __min_ram = None
    __min_disk = None
    __keep = False

    def __init__(self, export_cloud=None, import_cloud=None, vm_name=None, volume_id=None, snap_id=None, vm_size=None, newvol_id=None, image_id=None, image_filename=None, key_name=None, security_groups=None, flavor_name=None, subnet_names=None, ips=None, min_ram=None, min_disk=None, poll_sleep_time=None, poll_timeout=None):
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

        if vm_size is not None and vm_size != '':
            self.__vm_size = vm_size
        elif args.vm_size is not None and args.vm_size != '':
            self.__vm_size = args.vm_size

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

        if security_groups is not None and security_groups != '':
            self.__security_groups = security_groups
        elif args.security_groups is not None and args.security_groups != '':
            self.__security_groups = args.security_groups

        if flavor_name is not None and flavor_name != '':
            self.__flavor_name = flavor_name
        elif args.flavor_name is not None and args.flavor_name != '':
            self.__flavor_name = args.flavor_name

        if subnet_names is not None and subnet_names != '':
            self.__subnet_names = subnet_names
        elif args.subnet_names is not None and args.subnet_names != '':
            self.__subnet_names = args.subnet_names

        if ips is not None and ips != '':
            self.__ips = ips
        elif args.ips is not None and args.ips != '':
            self.__ips = args.ips

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
            elif self.__import_cloud is not None and self.__key_name is not None and self.__flavor_name is not None and self.__subnet_names is not None:
                self.__action = 'import'

    def __get_file_checksum(self, filename):
        result = None

        if verbose_level >= 2:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Calculating %s checksum...' %(dt, filename))
        res = hashlib.md5(open(filename, 'rb').read()).hexdigest()
        if res != '':
            result = res
            if verbose_level >= 3:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    %s: %s checksum: %s' %(dt, filename, result))
            elif verbose_level >= 2:
                print('')

        return result

    def __get_os_cmd_result(self, cloud, cmd, params):
        result = None

        no_format_cmds = ['server stop', 'volume delete', 'volume snapshot delete', 'image save', 'image delete', 'floating ip set']

        tmp_params = []
        if cmd not in no_format_cmds:
            tmp_params.append('-f json')
        tmp_params += params
        params = tmp_params

        if verbose_level >= 4:
            print('        openstack --os-cloud %s %s %s' %(cloud, cmd, ' '.join(params)))
        proc = subprocess.run(['openstack --os-cloud %s %s %s' %(cloud, cmd, ' '.join(params))], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        if proc.stderr != '':
            raise Exception(proc.stderr)

        try:
            if cmd not in no_format_cmds:
                result = json.loads(proc.stdout)
        except Exception as e:
            raise Exception(e)

        return result

    def __poll(self, cloud, cmd, params, key, expected_value, timeout, polling_sleep_time=None, nonexistence=False):
        result = False

        while result is False:
            tmp_results = None
            try:
                tmp_results = self.__get_os_cmd_result(cloud, cmd, params)
            except Exception as e:
                e = str(e).strip()
                if e.startswith('No ') and 'found' in e:
                    if nonexistence:
                        result = True
                        break

            if tmp_results is not None:
                if not isinstance(tmp_results, list):
                    tmp_results = [tmp_results]
                for tmp_result in tmp_results:
                    if expected_value is not None and tmp_result[key] == expected_value:
                        result = True
                        break
                    elif expected_value is None and (tmp_result[key] is None or tmp_result[key] == ''):
                        result = True
                if nonexistence and result is False:
                    result = True
            elif expected_value is None and tmp_results is None:
                result = True

            if not result:
                if polling_sleep_time is None:
                    polling_sleep_time = self.__polling_sleep_time
                time.sleep(polling_sleep_time)

        return result

    def __is_vm_active(self, cloud, vm):
        result = False

        if self.__get_os_cmd_result(cloud, 'server show', [vm])['status'] == 'ACTIVE':
            result = True

        return result

    def __vm_shutdown(self, cloud, vm):
        result = False

        res = self.__get_os_cmd_result(cloud, 'server stop', [vm])
        if verbose_level >= 2:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Waiting for server %s to stop...' %(dt, vm))
        res = self.__poll(cloud, 'server show', [vm], 'status', 'SHUTOFF', self.__polling_timeout)
        if res:
            result = True
            if verbose_level >= 2:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    %s: Server %s stopped successfully.' %(dt, vm))

        return result

    def __get_vm_info(self, cloud, vm):
        result = True

        if verbose_level >= 2:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Getting information about server %s' %(dt, vm))
        vm_info = self.__get_os_cmd_result(cloud, 'server show', [vm])

        if self.__key_name is None:
            key_name = None
            key_name = vm_info['key_name']
            if key_name is not None and key_name != '':
                self.__key_name = key_name
                print('    Key name: %s' %(self.__key_name))
            else:
                result = False

        if result and self.__security_groups is None:
            security_groups = vm_info['security_groups']
            if not isinstance(security_groups, list):
                security_groups = [security_groups]

            new_security_groups = []
            for security_group in security_groups:
                security_group = security_group['name']
                if security_group != '':
                    new_security_groups.append(security_group)

            if len(new_security_groups) > 0:
                self.__security_groups = ','.join(new_security_groups)
                if verbose_level >= 1:
                    print('    Security groups: %s' %(self.__security_groups))
            else:
                result = False

        if result and self.__flavor_name is None:
            flavor_name = vm_info['flavor']
            flavor_name = flavor_name.split()[0]
            if flavor_name is not None and flavor_name != '':
                self.__flavor_name = flavor_name
                if verbose_level >= 1:
                    print('    Flavor name: %s' %(self.__flavor_name))
            else:
                result = False

        if result and (self.__subnet_names is None or self.__ips is None):
            subnet_names = None
            ips = None
            addresses = vm_info['addresses']
            for subnet_name, subnet in addresses.items():
                if subnet_names is None:
                    subnet_names = ''
                if subnet_names != '':
                    subnet_names += ','
                subnet_names += subnet_name

                if len(subnet) > 0:
                    if ips is None:
                        ips = ''
                    if ips != '':
                        ips += ','
                    ips += subnet[0]

                    if len(subnet) > 1:
                        self.__has_floating = True
                        self.__floating_subnet = subnet_name

            if self.__subnet_names is None:
                if subnet_names is not None:
                    self.__subnet_names = subnet_names
                    if verbose_level >= 1:
                        print('    Subnet names: %s' %(self.__subnet_names))
                else:
                    result = False

            if self.__ips is None:
                if ips is not None:
                    self.__ips = ips
                    if verbose_level >= 1:
                        print('    IPs: %s' %(self.__ips))
                else:
                    result = False
                if self.__has_floating:
                    if verbose_level >= 1:
                        print('    Floating IP linked to NIC in subnet %s' %(self.__floating_subnet))

        if result and self.__volume_id is None:
            vol_id = None
            volumes = vm_info['volumes_attached']
            if volumes is not None and len(volumes) > 0:
                vol_id = volumes[0]['id']

            if vol_id is not None and vol_id != '':
                self.__volume_id = vol_id
                if verbose_level >= 2:
                    print('    Volume ID: %s' %(self.__volume_id))
            else:
                if verbose_level >= 2:
                    print('    WARNING: This VM has no attached volume!')
                if self.__flavor_name is not None and self.__vm_size is None:
                    result = self.__get_flavor_info(cloud, vm, self.__flavor_name)

        if result and self.__volume_id is not None:
            result = self.__get_volume_info(cloud, vm, self.__volume_id)

        return result

    def __get_volume_info(self, cloud, vm, volume_id):
        result = True

        if verbose_level >= 2:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Getting information about volume ID %s' %(dt, volume_id))
        volume_info = self.__get_os_cmd_result(cloud, 'volume show', [volume_id])
        if self.__vm_size is None:
            volume_size = None
            volume_size = volume_info['size']
            if volume_size is not None and volume_size != '':
                self.__vm_size = volume_size
                if verbose_level >= 1:
                    print('    Volume size: %s' %(self.__vm_size))
            else:
                result = False

        return result

    def __get_flavor_info(self, cloud, vm, flavor_id):
        result = True

        if verbose_level >= 2:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Getting information about flavor ID %s' %(dt, flavor_id))
        flavor_info = self.__get_os_cmd_result(cloud, 'flavor show', [flavor_id])
        if result and self.__vm_size is None:
            vm_size = None
            vm_size = flavor_info['disk']
            if vm_size is not None and vm_size != '':
                self.__vm_size = vm_size
                if verbose_level >= 1:
                    print('    VM disk size: %s' %(self.__vm_size))
            else:
                result = False

        return result

    def __create_snapshot(self, cloud, vm, volume_id):
        result = True

        if verbose_level >= 1:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Creating volume snapshot %s.bkp from volume ID %s...' %(dt, vm, volume_id))
        snap_id = None
        snap_id = self.__get_os_cmd_result(cloud, 'volume snapshot create', ['--volume %s' %(volume_id), '--force', '%s.bkp' %(vm)])['id']
        if snap_id is not None and snap_id != '':
            if verbose_level >= 2:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    Volume snapshot ID: %s' %(snap_id))
                print('    %s: Waiting for volume snapshot ID %s to be available...' %(dt, snap_id))
            res = self.__poll(cloud, 'volume snapshot show', [snap_id], 'status', 'available', self.__polling_timeout)
            if res:
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    %s: Volume snapshot ID %s available.' %(dt, snap_id))
            else:
                result = False
        else:
            result = False

        if result:
            self.__snap_id = snap_id

        return result

    def __create_snapshot_volume(self, cloud, vm, snap_id, volume_size):
        result = True

        if verbose_level >= 1:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Creating volume %s.bkp of size %s GiB from volume snapshot ID %s...' %(dt, vm, volume_size, snap_id))
        newvol_id = None
        newvol_id = self.__get_os_cmd_result(cloud, 'volume create', ['--snapshot %s' %(snap_id), '--size %s' %(volume_size), '%s.bkp' %(vm)])['id']
        if newvol_id is not None and newvol_id != '':
            if verbose_level >= 2:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    Volume ID: %s' %(newvol_id))
                print('    %s: Waiting for volume ID %s to be available...' %(dt, newvol_id))
            res = self.__poll(cloud, 'volume show', [newvol_id], 'status', 'available', self.__polling_timeout)
            if res:
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    %s: Volume ID %s available.' %(dt, newvol_id))
            else:
                result = False
        else:
            result = False

        if result:
            self.__newvol_id = newvol_id

        return result

    def __create_image(self, cloud, vm, newvol_id=None):
        result = True

        dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        if newvol_id is not None:
            if verbose_level >= 1:
                print('    %s: Creating image %s.bkp from volume ID %s...' %(dt, vm, newvol_id))
        elif self.__volume_id is None and self.__vm_size is not None:
            if verbose_level >= 1:
                print('    %s: Creating image %s.bkp from VM %s (no volume attached)...' %(dt, vm))
        else:
            raise Exception('Not enough information to go any further!')

        image_id = None
        tries = 0
        while image_id is None and tries < 2:
            result = True
            image_id = None
            try:
                if verbose_level >= 3:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    - %s: Try #%s...' %(dt, tries))
                cmd = ''
                params = []
                if newvol_id is None:
                    cmd += 'server '
                cmd = 'image create'
                if newvol_id is not None:
                    params.append('--volume %s' %(newvol_id))
                    params.append('--unprotected')
                    params.append('--container-format bare')
                    params.append('--disk-format %s' %(self.__image_format))
                else:
                    params.append('--name')
                params.append('%s.bkp' %(vm))
                if newvol_id is None:
                    params.append('%s' %(vm))

                image_id = self.__get_os_cmd_result(cloud, cmd, params)['image_id']
            except Exception as e:
                print(e)

            if image_id is not None and image_id != '':
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc)
                    print('    Image ID: %s' %(image_id))
                    print('    %s: Waiting for image ID %s to be active...' %(dt, image_id))

                res = False
                try:
                    res = self.__poll(cloud, 'image show', [image_id], 'status', 'active', self.__polling_timeout)
                except Exception as e:
                    print(e)

                if res:
                    image_checksum = None
                    image_checksum = self.__get_os_cmd_result(cloud, 'image show', [image_id])['checksum']
                    if image_checksum is not None and image_checksum != '':
                        self.__image_checksum = image_checksum
                    if verbose_level >= 2:
                        dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                        print('    %s: Image ID %s available (checksum: %s).' %(dt, image_id, self.__image_checksum))
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

        if verbose_level >= 1:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Saving image ID %s as file %s...' %(dt, image_id, filename))
        tries = 0
        res = False
        while res is not None:
            try:
                if verbose_level >= 3:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    - %s: Try #%s...' %(dt, tries))
                res = False
                res = self.__get_os_cmd_result(cloud, 'image save', ['--file %s' %(filename), image_id])
            except Exception as e:
                print(e)
            tries += 1

        if res is None:
            if os.path.exists(filename):
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    %s: Image ID %s saved successfully and available as file %s.' %(dt, image_id, filename))
                file_checksum = self.__get_file_checksum(filename)
                if file_checksum is not None and file_checksum != '':
                    self.__image_file_checksum = file_checksum
                    if self.__image_checksum is not None and self.__image_checksum != '':
                        if self.__image_file_checksum == self.__image_checksum:
                            self.__export_checksum_ok = True
                            if verbose_level >= 1:
                                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                                print('    %s: file %s checksum verification OK' %(dt, filename))
                        else:
                            result = False
                            if verbose_level >= 1:
                                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                                print('    %s: File %s checksum does NOT match image %s checksum!' %(dt, filename, image_id))
                    else:
                        if verbose_level >= 1:
                            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                            print('    %s: Warning: image %s checksum is not available! Cannot compare it with file %s checksum!' %(dt, image_id, filename))
                else:
                    if verbose_level >= 1:
                        dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                        print('    %s: Warning: error while calculating checksum for file %s! Cannot compare it with image %s checksum!' %(dt, filename, image_id))
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

        if verbose_level >= 1:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Creating image %s.rst from image file %s...' %(dt, vm, image_file))
        image_id = None
        tries = 0
        while image_id is None and tries < 2:
            result = True
            image_id = None
            try:
                if verbose_level >= 3:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    - %s: Try #%s...' %(dt, tries))
                image_id = self.__get_os_cmd_result(cloud, 'image create', ['--file %s' %(image_file), '--container-format bare', '--disk-format %s' %(image_format), '--min-ram %s' %(min_ram), '--min-disk %s' %(min_disk), '%s.rst' %(vm)])['id']
            except Exception as e:
                print(e)

            if image_id is not None and image_id != '':
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    Image ID: %s' %(image_id))
                    print('    %s: Waiting for image ID %s to be active...' %(dt, image_id))

                res = False
                try:
                    res = self.__poll(cloud, 'image show', [image_id], 'status', 'active', self.__polling_timeout)
                except Exception as e:
                    print(e)

                if res:
                    image_checksum = None
                    image_checksum = self.__get_os_cmd_result(cloud, 'image show', [image_id])['checksum']
                    if image_checksum is not None and image_checksum != '':
                        if self.__image_checksum is None:
                            self.__image_checksum = image_checksum

                        if verbose_level >= 3:
                            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                            print('    %s: image %s checksum: %s' %(dt, image_id, image_checksum))
                        if self.__image_file_checksum is None:
                            self.__image_file_checksum = self.__get_file_checksum(filename)
                        if self.__image_file_checksum is not None and self.__image_file_checksum != '':
                            if image_checksum == self.__image_file_checksum:
                                self.__import_checksum_ok = True
                                if verbose_level >= 1:
                                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                                    print('    %s: image %s checksum verification OK' %(dt, image_id))
                            else:
                                result = False
                                if verbose_level >= 1:
                                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                                    print('    %s: Image %s checksum does NOT match file %s checksum!' %(dt, image_id, filename))
                        else:
                            if verbose_level >= 1:
                                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                                print('    %s: Warning: file %s checksum is not available! Cannot compare it with image %s checksum!' %(dt, filename, image_id))
                    if verbose_level >= 2:
                        dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                        print('    %s: Image ID %s available.' %(dt, image_id))
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

        if verbose_level >= 1:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Creating bootable volume %s of size %s GB from image ID %s...' %(dt, vm, volume_size, image_id))
        volume_id = self.__get_os_cmd_result(cloud, 'volume create', ['--image %s' %(image_id), '--size %s' %(volume_size), '--bootable', vm])['id']
        if volume_id != '':
            if verbose_level >= 2:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    Volume ID: %s' %(volume_id))
                print('    %s: Waiting for volume ID %s to be available...' %(dt, volume_id))
            res = self.__poll(cloud, 'volume show', [volume_id], 'status', 'available', self.__polling_timeout)
            if res:
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    %s: Volume ID %s available.' %(dt, volume_id))
            else:
                result = False
        else:
            result = False

        if result:
            self.__volume_id = volume_id

        return result

    def __create_vm(self, cloud, vm, volume_id, key_name, security_groups, flavor_name, subnet_names, ips=None):
        result = True

        if verbose_level >= 1:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('    %s: Creating VM %s from volume ID %s...' %(dt, vm, volume_id))
        vm_id = None

        params = []
        params.append('--flavor %s' %(flavor_name))
        params.append('--volume %s' %(volume_id))

        if security_groups is not None and security_groups != '':
            security_groups = security_groups.split(',')
        if subnet_names is not None and subnet_names != '':
            subnet_names = subnet_names.split(',')
        if ips is not None and ips != '':
            ips = ips.split(',')

        i = 0
        for subnet_name in subnet_names:
            fixed_ip_opt = ''
            if ips is not None and len(ips) == len(subnet_names):
                fixed_ip_opt = ',v4-fixed-ip=%s' %(ips[i])
            params.append('--nic net-id=%s%s' %(subnet_name, fixed_ip_opt))
            i += 1

        for security_group in security_groups:
            params.append('--security-group %s' %(security_group))

        params.append('--key-name %s' %(key_name))
        params.append(vm)

        vm_id = None
        vm_id = self.__get_os_cmd_result(cloud, 'server create', params)['id']
        if vm_id is not None and vm_id != '':
            if verbose_level >= 2:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    VM ID: %s' %(vm_id))
                print('    %s: Waiting for VM ID %s to be available...' %(dt, vm_id))
            res = self.__poll(cloud, 'server show', [vm_id], 'status', 'ACTIVE', self.__polling_timeout)
            if res:
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    %s: VM %s (ID %s) available.' %(dt, vm, vm_id))
            else:
                result = False
        else:
            result = False

        if result:
            self.__vm_id = vm_id

        return result

    def __assign_floating(self, cloud, vm_id, floating_subnet):
        result = False

        self.__subnet_names = None
        self.__ips = None
        self.__get_vm_info(cloud, vm_id)

        subnet_names = None
        ips = None
        if self.__subnet_names is not None and self.__subnet_names != '':
            subnet_names = self.__subnet_names.split(',')
        if self.__ips is not None and self.__ips != '':
            ips = self.__ips.split(',')

        fixed_ip = None
        if ips is not None and subnet_names is not None and len(ips) == len(subnet_names):
            i = 0
            for subnet_name in subnet_names:
                if subnet_name == floating_subnet:
                    fixed_ip = ips[i]
                i += 1
        port_id = None
        if fixed_ip is not None and fixed_ip != '':
            port_id = self.__get_os_cmd_result(cloud, 'port list', ['--server %s' %(vm_id), '--network %s' %(floating_subnet)])[0]['ID']

        floating_ip = None
        floating_ips = self.__get_os_cmd_result(cloud, 'floating ip list', ['--status DOWN'])
        if len(floating_ips) > 0:
            floating_ip = floating_ips[0]['Floating IP Address']
        if floating_ip is None:
            floating_ip = self.__get_os_cmd_result(cloud, 'floating ip create', [external_network])['floating_ip_address']

        if floating_ip is not None and fixed_ip is not None and port_id is not None:
            if verbose_level >= 1:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    %s: Assigning floating IP %s to server %s, on its NIC %s (port ID %s), on subnet %s...' %(dt, floating_ip, self.__vm_name, fixed_ip, port_id, floating_subnet))
            self.__get_os_cmd_result(cloud, 'floating ip set', ['--fixed-ip-address %s' %(fixed_ip), '--port %s' %(port_id), floating_ip])

            check = self.__get_os_cmd_result(cloud, 'floating ip list', ['--fixed-ip-address %s' %(fixed_ip)])
            if check is not None and len(check) > 0:
                result = True
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    %s: Floating IP assigned successfully.' %(dt))

        return result

    def __clean_up(self, cloud, image_id=None, newvol_id=None, snap_id=None):
        result = True

        if verbose_level >= 1:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('%s: Cleaning up...' %(dt))

        if image_id is not None:
            if verbose_level >= 2:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    %s: Deleting image ID %s...' %(dt, image_id))
            self.__get_os_cmd_result(cloud, 'image delete', [image_id])
            res = self.__poll(cloud, 'image show', [image_id], 'id', None, self.__polling_timeout, True)
            if res:
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    %s: Image ID %s successfully deleted.' %(dt, image_id))
            else:
                result = False

        if newvol_id is not None:
            if verbose_level >= 2:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    %s: Deleting volume ID %s...' %(dt, newvol_id))
            self.__get_os_cmd_result(cloud, 'volume delete', [newvol_id])
            res = self.__poll(cloud, 'volume show', [newvol_id], 'id', None, self.__polling_timeout, True)
            if res:
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    %s: Volume ID %s successfully deleted.' %(dt, newvol_id))
            else:
                result = False

        if snap_id is not None:
            if verbose_level >= 2:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    %s: Deleting volume snapshot ID %s...' %(dt, snap_id))
            self.__get_os_cmd_result(cloud, 'volume snapshot delete', [snap_id])
            res = self.__poll(cloud, 'volume snapshot show', [snap_id], 'id', None, self.__polling_timeout, True)
            if res:
                if verbose_level >= 2:
                    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    print('    %s: Volume snapshot ID %s successfully deleted.' %(dt, snap_id))
            else:
                result = False

        return result

    def __export(self):
        if verbose_level >= 1:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('%s: Preparing export of VM %s from cloud %s...' %(dt, self.__vm_name, self.__export_cloud))

        go_ahead = True

        if self.__image_file is None and self.__image_id is None and self.__newvol_id is None and self.__snap_id is None and self.__is_vm_active(self.__export_cloud, self.__vm_name):
            if verbose_level >= 2:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('    %s: Server %s is ACTIVE! Stopping it...' %(dt, self.__vm_name))
            go_ahead = self.__vm_shutdown(self.__export_cloud, self.__vm_name)

        if go_ahead:
            if self.__action == 'export' and self.__volume_id is None:
                go_ahead = self.__get_vm_info(self.__export_cloud, self.__vm_name)
            elif self.__action == 'transfer' and self.__volume_id is None and self.__key_name is None and self.__security_groups is None and self.__subnet_names is None:
                go_ahead = self.__get_vm_info(self.__export_cloud, self.__vm_name)

        if go_ahead and self.__image_file is None and self.__image_id is None and self.__newvol_id is None and self.__snap_id is None and self.__volume_id is not None:
            go_ahead = self.__create_snapshot(self.__export_cloud, self.__vm_name, self.__volume_id)

        if go_ahead and self.__image_file is None and self.__image_id is None and self.__newvol_id is None and self.__volume_id is not None:
            go_ahead = self.__create_snapshot_volume(self.__export_cloud, self.__vm_name, self.__snap_id, self.__vm_size)

        if go_ahead and self.__image_file is None and self.__image_id is None:
            go_ahead = self.__create_image(self.__export_cloud, self.__vm_name, self.__newvol_id)

        if go_ahead and self.__image_file is None:
            go_ahead = self.__save_image(self.__export_cloud, self.__vm_name, self.__image_id, self.__image_filename)

        if not self.__keep and (self.__image_id is not None or self.__newvol_id is not None or self.__snap_id is not None):
            go_ahead = self.__clean_up(self.__export_cloud, self.__image_id, self.__newvol_id, self.__snap_id)

        return go_ahead

    def __import(self):
        if verbose_level >= 1:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print('%s: Preparing import of VM %s (file %s) in cloud %s...' %(dt, self.__vm_name, self.__image_file, self.__import_cloud))

        go_ahead = True

        if self.__image_file is not None and self.__image_format is not None and self.__min_ram is not None and self.__min_disk is not None and self.__vm_name is not None and self.__image_id is None:
            go_ahead = self.__import_image(self.__import_cloud, self.__vm_name, self.__image_file, self.__image_format, self.__min_ram, self.__min_disk)
            if go_ahead and self.__action == 'transfer':
                if self.__export_checksum_ok and self.__import_checksum_ok:
                    if verbose_level >= 1:
                        dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                        print('    %s: VM %s image transfer done successfully.' %(dt, self.__vm_name))

        if go_ahead and self.__vm_name is not None and self.__min_disk is not None and self.__image_id is not None and self.__volume_id is None:
            go_ahead = self.__create_image_volume(self.__import_cloud, self.__vm_name, self.__image_id, self.__min_disk)

        if go_ahead and self.__vm_name is not None and self.__volume_id is not None and self.__key_name is not None and self.__security_groups is not None and self.__flavor_name is not None and self.__subnet_names is not None:
            go_ahead = self.__create_vm(self.__import_cloud, self.__vm_name, self.__volume_id, self.__key_name, self.__security_groups, self.__flavor_name, self.__subnet_names, self.__ips)

        if go_ahead and self.__vm_id is not None:
            if self.__has_floating and self.__floating_subnet is not None:
                go_ahead = self.__assign_floating(self.__import_cloud, self.__vm_id, self.__floating_subnet)

        if not self.__keep and self.__image_id is not None:
            go_ahead = self.__clean_up(self.__import_cloud, self.__image_id)

        return go_ahead

    def run(self):
        result = False

        if self.__action is not None:
            if self.__action == 'export':
                result = self.__export()
            elif self.__action == 'import':
                result = self.__import()
            elif self.__action == 'transfer':
                result = self.__export()

                self.__volume_id = None
                self.__snap_id = None
                self.__newvol_id = None
                self.__image_id = None

                if result:
                    result = self.__import()
        else:
            sys.exit('No action can be done!')

        if result:
            if verbose_level >= 1:
                dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                print('%s: %s done successfully.' %(dt, self.__action.capitalize()))
        else:
            dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            sys.exit('%s: FAILED!' %(dt))

def main():
    osvm = OSVM()
    osvm.run()

if __name__ == '__main__':
    main()
