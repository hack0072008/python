#!/usr/bin/python
#-*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2017 , Inc.
# All Rights Reserved.


import datetime
import time
from boto import ec2
from boto import rds2
from boto import elasticache
from boto import s3
from boto.ec2 import cloudwatch
from boto.ec2 import autoscale
import boto3


class HandlerASG(object):
    def __init__(self, region_name, ec2_access_key_id, ec2_access_key_value, env_type):
        self.region_name = region_name
        self.ec2_access_key_id = ec2_access_key_id
        self.ec2_access_key_value = ec2_access_key_value
        self.env_type = env_type
        self.conn = None
        self.region = None
        return

    def connect(self):
        if self.conn:
            return
        try:
            self.conn = ec2.autoscale.connect_to_region(self.region_name, aws_access_key_id=self.ec2_access_key_id, aws_secret_access_key=self.ec2_access_key_value)
        except Exception as e:
            print 'connect to aws ASG failed, %s' % e
        return

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        return
 
    def get_groups(self):
        groups = self.conn.get_all_groups()
        values = []
        for group in groups:
            value = {
                'group_name': group.name,
                'group_zones ': group.availability_zones,
                'group_capacity': group.desired_capacity,
                'group_max_size': group.max_size,
                'group_min_size': group.min_size,
                'group_cooldown': group.default_cooldown,
                'group_tag_module': [tag.value for tag in group.tags if tag.key == 'module'][0] if [tag.value for tag in group.tags if tag.key == 'module'] else None,
                'group_tag_version': [tag.value for tag in group.tags if tag.key == 'sub_version'][0] if [tag.value for tag in group.tags if tag.key == 'sub_version'] else None,
                'group_tag_env': [tag.value for tag in group.tags if tag.key == 'env_type'][0] if [tag.value for tag in group.tags if tag.key == 'env_type'] else None,
            }
            values.append(value)
        return values

    def get_groups_info(self):
        groups = self.conn.get_all_groups()
        values = []
        for group in groups:
            value = {
                'group_tag_module': [tag.value for tag in group.tags if tag.key == 'module'][0] if [tag.value for tag in group.tags if tag.key == 'module'] else None,
                'group_tag_version': [tag.value for tag in group.tags if tag.key == 'sub_version'][0] if [tag.value for tag in group.tags if tag.key == 'sub_version'] else None,
                'group_tag_env': [tag.value for tag in group.tags if tag.key == 'env_type'][0] if [tag.value for tag in group.tags if tag.key == 'env_type'] else None,
            }
            values.append(value)
        return values

    def get_group_name(self, module):
        groups = self.conn.get_all_groups()
        values = []
        for group in groups:
            search = 0
            for tag in group.tags:
                if tag.key == 'module' and tag.value == module:
                    search += 1
                if tag.key == 'env_type' and tag.value == self.env_type:
                    search += 1
            if search == 2:
                print 'warnning: ASG model[%s] env_type[%s] group found [%d], name[%s].' % (module, self.env_type, search/2, group.name)
                return group.name
        return None

    def get_group_names(self, module):
        groups = self.conn.get_all_groups()
        values = []
        for group in groups:
            search = 0
            for tag in group.tags:
                if tag.key == 'module' and tag.value == module:
                    search += 1
                if tag.key == 'env_type' and tag.value == self.env_type:
                    search += 1
            if search == 2:
                values.append(group.name)
        print 'warnning: ASG model[%s] env_type[%s] group found [%d], names:[%s].' % (module, self.env_type, len(values), ','.join(values))
        return values

    def set_groups_size(self, module, desired_capacity, min_size, max_size):
        group_name = self.get_group_name(module)
        if not group_name:
            self.LOG.error('module [%s] has not match asg' % module)
            return

        self.conn.create_scheduled_group_action(
            group_name,
            'default',
            desired_capacity = desired_capacity,
            min_size = min_size,
            max_size = max_size,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -(60 * 60 * 8 - 10)),
            #end_time = 
            #recurrence = '* * * * *'
            )
        return

    def get_group_all_instans(self, module):
        instance_ids = []
        name = self.get_group_name(module)
        if name:
            group = self.conn.get_all_groups(names = [name])[0]
            instance_ids = [i.instance_id for i in group.instances]
        return instance_ids

    def get_group_healthy_instans(self, module):
        instance_ids = []
        name = self.get_group_name(module)
        if name:
            group = self.conn.get_all_groups(names = [name])[0]
            instance_ids = [i.instance_id for i in group.instances if i.health_status == 'Healthy' and i.lifecycle_state == 'InService']
        return instance_ids

    def get_groups_healthy_instans(self, module):
        instance_ids = []
        names = self.get_group_names(module)
        if names:
            for name in names:
                group = self.conn.get_all_groups(names = [name])[0]
                inst_ids = [i.instance_id for i in group.instances if i.health_status == 'Healthy' and i.lifecycle_state == 'InService']
                instance_ids.extend(inst_ids)
        return instance_ids

class HandlerCloudWatch(object):
    def __init__(self, region_name, ec2_access_key_id, ec2_access_key_value):
        self.region_name = region_name
        self.ec2_access_key_id = ec2_access_key_id
        self.ec2_access_key_value = ec2_access_key_value
        self.conn = None
        self.region = None
        self.conn_sqs = None
        return

    def connect(self):
        if self.conn:
            return
        try:
            self.region = ec2.get_region(self.region_name)
            self.conn = ec2.cloudwatch.connect_to_region(self.region_name, aws_access_key_id=self.ec2_access_key_id, aws_secret_access_key=self.ec2_access_key_value)
        except Exception as e:
            print 'connect to aws cloudwatch failed, %s' % e
        return

    def sqs_connect(self):
        if self.conn_sqs:
            return
        try:
            #self.region = ec2.get_region(self.region)
            self.conn_sqs = boto3.client('cloudwatch', region_name=self.region_name, aws_access_key_id=self.ec2_access_key_id, aws_secret_access_key=self.ec2_access_key_value)
        except Exception as e:
            print 'connect to aws sqs cloudwatch failed, %s' % e
        return

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        return

    def get_cpu_value(self, instance_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'CPUUtilization',
            namespace = 'AWS/EC2',
            statistics = ['Average'],
            dimensions = {'InstanceId': instance_id},
            unit = 'Percent'
        )
        try:
            return float(format(rsp[0]['Average'], '.2f'))
        except:
            return 0

    def get_mem_value(self, instance_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'MemoryUtilization',
            namespace = 'System/Linux',
            statistics = ['Average'],
            dimensions = {'InstanceId': instance_id},
            unit = 'Percent'
        )
        try:
            return float(format(rsp[0]['Average'], '.2f'))
        except:
            return 0

    def get_network_out(self, instance_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'NetworkOut',
            namespace = 'AWS/EC2',
            statistics = ['Average'],
            dimensions = {'InstanceId': instance_id},
            unit = 'Bytes'
        )
        try:
            return float(format(rsp[0]['Average'] / 1024, '.3f'))
        except:
            return 0

    def get_root_space(self, instance_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'DiskSpaceAvailable',
            namespace = 'System/Linux',
            statistics = ['Average'],
            dimensions = {'InstanceId': instance_id, 'MountPath': '/', 'Filesystem': '/dev/xvda1'},
            unit = 'Gigabytes'
        )
        try:
            return float(format(rsp[0]['Average'], '.3f'))
        except:
            return 99

    def get_log_attempt(self, instance_id, file_system):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'DiskSpaceAvailable',
            namespace = 'System/Linux',
            statistics = ['Average'],
            dimensions = {'InstanceId': instance_id, 'MountPath': '/var/log', 'Filesystem': file_system},
            unit = 'Gigabytes'
        )
        return rsp

    def get_log_space(self, instance_id):
        log_file_systems = ['/dev/xvdf1', '/dev/xvdc', '/dev/xvdc1']
        log_space_remain = 0
        for log_file_system in log_file_systems:
            rsp = self.get_log_attempt(instance_id, log_file_system)
            try:
                log_space_remain = float(format(rsp[0]['Average'], '.3f'))
            except:
                continue
        return log_space_remain if log_space_remain else 99

    def get_tmp_attempt(self, instance_id, file_system):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'DiskSpaceAvailable',
            namespace = 'System/Linux',
            statistics = ['Average'],
            dimensions = {'InstanceId': instance_id, 'MountPath': '/tmp', 'Filesystem': file_system},
            unit = 'Gigabytes'
        )
        return rsp

    def get_tmp_space(self, instance_id):
        tmp_file_systems = ['/dev/xvdc', '/dev/xvdb', '/dev/xvdb1']
        tmp_space_remain = 0
        for tmp_file_system in tmp_file_systems:
            rsp = self.get_tmp_attempt(instance_id, tmp_file_system)
            try:
                tmp_space_remain = float(format(rsp[0]['Average'], '.3f'))
            except:
                continue
        return tmp_space_remain if tmp_space_remain else 99               

    def get_rds_cpu(self, dbinstance_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'CPUUtilization',
            namespace = 'AWS/RDS',
            statistics = ['Average'],
            dimensions = {'DBInstanceIdentifier': dbinstance_id},
            unit = 'Percent'   
        )
        try:
            return float(format(rsp[0]['Average'], '.2f'))
        except:
            return 0

    def get_rds_con(self, dbinstance_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'DatabaseConnections',
            namespace = 'AWS/RDS',
            statistics = ['Average'],
            dimensions = {'DBInstanceIdentifier': dbinstance_id},
            unit = 'Count'
        )
        try:
            return int(rsp[0]['Average'])
        except:
            return 0

    def get_rds_mem(self, dbinstance_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'FreeableMemory',
            namespace = 'AWS/RDS',
            statistics = ['Average'],
            dimensions = {'DBInstanceIdentifier': dbinstance_id}
            #unit = 'Megabytes'
        )
        try:
            mem_val = float(format(rsp[0]['Average'] / 1024 / 1024, '.2f'))
            return mem_val
        except:
            return 0

    def get_rds_swap(self, dbinstance_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'SwapUsage',
            namespace = 'AWS/RDS',
            statistics = ['Average'],
            dimensions = {'DBInstanceIdentifier': dbinstance_id}
            #unit = 'Megabytes'
        )
        try:
            return float(format(rsp[0]['Average'] / 1024 / 1024, '.2f'))
        except:
            return 0

    def get_rds_disk(self, dbinstance_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'FreeStorageSpace',
            namespace = 'AWS/RDS',
            statistics = ['Average'],
            dimensions = {'DBInstanceIdentifier': dbinstance_id}
            #unit = 'Megabytes'
        )
        try:
            return float(format(rsp[0]['Average'] / 1024 / 1024, '.2f'))
        except:
            return 0

    def get_ecache_cpu(self, ecache_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'CPUUtilization',
            namespace = 'AWS/ElastiCache',
            statistics = ['Average'],
            dimensions = {'CacheClusterId': ecache_id},
            unit = 'Percent'
        )
        try:
            return float(format(rsp[0]['Average'], '.2f'))
        except:
            return 0

    def get_ecache_con(self, ecache_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'CurrConnections',
            namespace = 'AWS/ElastiCache',
            statistics = ['Average'],
            dimensions = {'CacheClusterId': ecache_id},
            unit = 'Count'
        )
        try:
            return int(rsp[0]['Average'])
        except:
            return 0

    def get_ecache_mem(self, ecache_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'FreeableMemory',
            namespace = 'AWS/ElastiCache',
            statistics = ['Average'],
            dimensions = {'CacheClusterId': ecache_id}
            #unit = 'Megabytes'
        )
        try:
            return float(format(rsp[0]['Average'] / 1024 / 1024, '.2f'))
        except:
            return 0

    def get_ecache_swap(self, ecache_id):
        rsp = self.conn.get_metric_statistics(
            period = 300,
            start_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8 - 60 * 10),
            end_time = datetime.datetime.now() + datetime.timedelta(seconds = -60 * 60 * 8),
            metric_name = 'SwapUsage',
            namespace = 'AWS/ElastiCache',
            statistics = ['Average'],
            dimensions = {'CacheClusterId': ecache_id}
            #unit = 'Megabytes'
        )
        try:
            return float(format(rsp[0]['Average'] / 1024 / 1024, '.2f'))
        except:
            return 0

    def get_sqs_queue_metrics(self, metrics_name=None, queue_name=None, unit_type=None, start_time=None, end_time=None):
        '''
        unit_type: Bytes/Count/Percent
        '''
        rsp = self.conn_sqs.get_metric_statistics(
            Namespace = 'AWS/SQS',
            Period = 300,
            MetricName = metrics_name,
            StartTime = start_time,
            EndTime = end_time,
            Statistics = ['Average'],
            Unit = unit_type,
            Dimensions = [ {'Name' : 'QueueName', 'Value' : queue_name } ] 
        )
        #print 'in get_sqs_queue_metrics: unit_type[%s] rsp[%s]' % (unit_type,rsp)
        try:
            if unit_type == 'Percent':
                if len(rsp['Datapoints']) == 0:
                    return float(format('0', '.2f'))
                return float(format(rsp['Datapoints'][0]['Average'] , '.2f'))
            if unit_type == 'Count' or unit_type == 'Bytes':
                if len(rsp['Datapoints']) == 0:
                    return int(0)
                return int(rsp['Datapoints'][0]['Average'])
        except:
            return 0

class HandlerEc2(object):
    def __init__(self, region_name, ec2_access_key_id, ec2_access_key_value):
        self.region_name = region_name
        self.ec2_access_key_id = ec2_access_key_id
        self.ec2_access_key_value = ec2_access_key_value
        self.conn = None
        return

    def connect(self):
        if self.conn:
            return
        try:
            self.conn = ec2.connect_to_region(self.region_name, aws_access_key_id=self.ec2_access_key_id, aws_secret_access_key=self.ec2_access_key_value)
        except Exception as e:
            print "%s: connect to aws ec2 failed, may be not in aws ec2?" % e
        return

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        return

    def set_filters_status(self, status):
        self.filters = [{
            'Name': 'instance-state-name',
            'Values': [status]
        }]
        return

    def set_filters_env(self, env):
        if self.region_name == 'cn-north-1' and env == 'production':
            env = 'prod'
        if self.region_name == 'eu-central-1' and env == 'production':
            env = 'prod'
        if self.region_name == 'ap-southeast-2' and env == 'production':
            env = 'prod'
        if self.region_name == 'us-west-2' and env == 'production':
            env = 'prod'
        self.filters = [{
            'Name': 'tag:env_type',
            #'Values': ['prod' if self.region_name == 'cn-north-1' and env == 'production' else env]
            'Values': env,
        }]
        return

    def set_filters_id(self, instance_id):
        self.filters = {
            'instance-id': instance_id
        }
        return

    def set_filters_status_env(self, status, env):
        if self.region_name == 'cn-north-1' and env == 'production':
            env = 'prod'
        if self.region_name == 'eu-central-1' and env == 'production':
            env = 'prod'
        if self.region_name == 'ap-southeast-2' and env == 'production':
            env = 'prod'
        if self.region_name == 'us-west-2' and env == 'production':
            env = 'prod'
        self.filters = {
            'instance-state-name': status,
            #'tag:env_type': 'prod' if self.region_name == 'cn-north-1' and env == 'production' else env,
            'tag:env_type': env,
        }
        return

    def get_instance(self):
        instances_info = []
        if self.conn:
            instances = self.conn.get_only_instances(
                filters=self.filters
            )
            for instance in instances:
                public_addr = instance.ip_address if instance.ip_address else 'null'
                private_addr = instance.private_ip_address if instance.ip_address else 'null'

                try:
                    tag_module = instance.tags['module']
                except:
                    tag_module = 'null'

                try:
                    tag_sub_version = instance.tags['sub_version']
                except:
                    tag_sub_version = 'null'

                try:
                    tag_debug = instance.tags['debug']
                except:
                    tag_debug = 'null'

                instance_info = {
                    'id': (instance.id).encode('ascii'),
                    'instance_type': (instance.instance_type).encode('ascii'),
                    'public_ip_address': (public_addr).encode('ascii'),
                    'private_ip_address': (private_addr).encode('ascii'),
                    'availability_zone': (instance.placement).encode('ascii'),
                    'tag_module': (tag_module).encode('ascii'),
                    'tag_sub_version': (tag_sub_version).encode('ascii'),
                    'tag_debug': (tag_debug).encode('ascii'),
                }
                instances_info.append(instance_info)
        return instances_info

    def get_instances_from_ids(self, instance_ids):
        instances = []
        if self.conn:
            instances = self.conn.get_only_instances(instance_ids)
        return instances

class HandlerRDS(object):
    def __init__(self, region_name, rds_access_key_id, rds_access_key_value):
        self.region_name = region_name
        self.rds_access_key_id = rds_access_key_id
        self.rds_access_key_value = rds_access_key_value
        self.conn = None
        return

    def connect(self):
        if self.conn:
            return
        try:
            self.conn = rds2.connect_to_region(self.region_name, aws_access_key_id=self.rds_access_key_id, aws_secret_access_key=self.rds_access_key_value)
        except Exception as e:
            print "%s: connect to aws rds failed, may be not in aws rds?" % e
        return

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        return

    def get_ids(self, endpoint):
        rds_ids = []
        instances = self.conn.describe_db_instances()
        print instances
        try:
            for instance in instances['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']:
                if instance['Endpoint']['Address'] == endpoint:
                    rds_ids.append(instance['DBInstanceIdentifier'])
                    break
        except:
            pass
        return rds_ids

    def get_instance(self):
        instances_info = []
        instances = self.conn.describe_db_instances()
        for instance in instances['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']:
            instance_info = {
                'id': instance['DBInstanceIdentifier'],
                'instance_engine': instance['Engine'],
                'instance_version': instance['EngineVersion'],
                'instance_type': instance['DBInstanceClass'],
                'instance_endpoint': instance['Endpoint']['Address'],
                'instance_storage': instance['AllocatedStorage']
            }
            instances_info.append(instance_info)
        return instances_info

class HandlerElastiCache(object):
    def __init__(self, region_name, ecache_access_key_id, ecache_access_key_value):
        self.region_name = region_name
        self.ecache_access_key_id = ecache_access_key_id
        self.ecache_access_key_value = ecache_access_key_value
        self.conn = None
        return

    def connect(self):
        if self.conn:
            return
        try:
            self.conn = elasticache.connect_to_region(self.region_name, aws_access_key_id=self.ecache_access_key_id, aws_secret_access_key=self.ecache_access_key_value)
        except Exception as e:
            print "%s: connect to aws elasticache failed, may be not in aws ecache?" % e
        return

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        return

    def get_ids(self, endpoint):
        ecache_ids = []
        instances = self.conn.describe_replication_groups()
        try:
            for instance in instances['DescribeReplicationGroupsResponse']['DescribeReplicationGroupsResult']['ReplicationGroups']:
                if instance['NodeGroups'][0]['PrimaryEndpoint']['Address'] == endpoint:
                    ecache_ids = instance['MemberClusters']
                    break
        except:
            pass
        return ecache_ids

    def get_instance(self, ecache_ids):
        instances_info = []
        for instance_id in ecache_ids:
            instance = self.conn.describe_cache_clusters(cache_cluster_id = instance_id)
            instance_info = {
                'id': instance_id,
                'instance_engine': instance['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters'][0]['Engine'],
                'instance_version': instance['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters'][0]['EngineVersion'],
                'instance_type': instance['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters'][0]['CacheNodeType']
            }
            instances_info.append(instance_info)
        return instances_info

class S3Handler(object):
    def __init__(self, region_name, access_key_id, secret_access_key, LOG = None):
        self.region_name = region_name
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.bucket_name = None
        self.bucket = None
        self.conn = None
        self.region = None
        self.LOG = LOG
        return

    def connect(self):
        if self.conn:
            return
        try:
            self.conn = boto3.resource(
                's3',
                region_name = self.region_name,
                aws_access_key_id = self.access_key_id,
                aws_secret_access_key = self.secret_access_key
            )
        except Exception as e:
            self.LOG.error('connect to aws s3 failed, {0}'.format(e))
        return

    def get_file(self, bucket_name, remote_path_file, local_path_file):
        self.bucket = self.conn.Bucket(bucket_name)
        self.bucket.download_file(remote_path_file, local_path_file)
        return

    def put_file(self, bucket_name, remote_path_file, local_path_file):
        self.bucket = self.conn.Bucket(bucket_name)
        self.bucket.upload_file(local_path_file, remote_path_file)
        return

class DynamodbHandler(object):
    def __init__(self, region_name, access_key_id, secret_access_key, LOG = None):
        self.region_name = region_name
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.conn = None
        self.LOG = LOG
        return

    def connect(self):
        if self.conn:
            return
        try:
            self.conn = boto3.resource(
                'dynamodb',
                region_name = self.region_name,
                aws_access_key_id = self.access_key_id,
                aws_secret_access_key = self.secret_access_key
            )
        except Exception as e:
            self.LOG.error('connect to aws dynamodb failed, {0}'.format(e))
        return

    def add_item(self, table_name =  None, item = None):
        if not table_name or not item:
            self.LOG.error('dynamodb: add_item check params failed.')
            return False
        if type(item) is not dict:
            self.LOG.error('dynamodb: add_item item is not dict:{0}'.format(type(item)))
            return False

        try:
            response = self.conn.Table(table_name).put_item(Item = item)
        except Exception as e:
            self.LOG.error('dynamodb: add_item call aws Dynamodb exception:{0}'.format(e))
            return False

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False

    def delete_item(self, table_name =  None, item_key = None, item_value = None):
        if not table_name or not item_key or not item_value:
            self.LOG.error('dynamodb: delete_item check params failed.')
            return False

        try:
            response = self.conn.Table(table_name).delete_item( Key = { item_key:item_value } )
        except Exception as e:
            self.LOG.error('dynamodb: delete_item call aws Dynamodb exception:{0}'.format(e))
            return False

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False

    def get_item(self, table_name =  None, item_key = None, item_value = None):
        if not table_name or not item_key or not item_value:
            self.LOG.error('dynamodb: get_item check params failed.')
            return False

        try:
            response = self.conn.Table(table_name).get_item( Key = { item_key:item_value } )
        except Exception as e:
            self.LOG.error('dynamodb: get_item call aws Dynamodb exception:{0}'.format(e))
            return False

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print 'dynamodb: get_item resopnse:'
            print response
            return response['Item']
        else:
            return False

    def scan_all(self, table_name =  None, conditions = None, item_filter = None ):
        if not table_name:
            self.LOG.error('dynamodb: get_item check params failed.')
            return False
        if not item_filter:
            item_filter = {}
        if not conditions:
            conditions = {}

        try:
            response = self.conn.Table(table_name).scan( Select = 'ALL_ATTRIBUTES', KeyConditions = conditions, ScanFilter=item_filter )
        except Exception as e:
            self.LOG.error('dynamodb: scan_all call aws Dynamodb exception:{0}'.format(e))
            return False

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print 'dynamodb: scan_all resopnse:'
            print response
            return response['Item']
        else:
            return False

class HandlerDynamodb(object):
    def __init__(self, region, access_key_id, access_key_value ):
        self.region = region
        self.access_key_id = access_key_id
        self.access_key_value = access_key_value
        self.dynamodb = None
        return

    def connect(self):
        if self.dynamodb:
            return
        try:
            #print self.region,self.access_key_id,self.access_key_value,self.queue_name_prefix
            self.dynamodb = boto3.resource('dynamodb', region_name = self.region, aws_access_key_id = self.access_key_id, aws_secret_access_key = self.access_key_value)
        except Exception as e:
            print 'connect to aws dynamodb failed, %s' % e
        return

    def get_dynamodb_table_all_items(self, table_name = None):
        if self.dynamodb and table_name:
            items = []
            try:
                table = self.dynamodb.Table( table_name )
                resp = table.scan( Select='ALL_ATTRIBUTES' )
                if resp['Count'] != 0:
                    items = resp['Items'] 
                else:
                    items = []
            except Exception as e:
                print 'get aws dynamodb table all items failed, %s' % str(e)
            return items
        else:
            return

class HandlerRoute53(object):
    def __init__(self, region, access_key_id, access_key_value, hosted_zone_id):
        self.region = region
        self.access_key_id = access_key_id
        self.access_key_value = access_key_value
        self.route53 = None
        self.hosted_zone_id = hosted_zone_id
        return

    def connect(self):
        if self.route53:
            return
        try:
            #print self.region,self.access_key_id,self.access_key_value
            self.route53 = boto3.client('route53', region_name = self.region, aws_access_key_id = self.access_key_id, aws_secret_access_key = self.access_key_value)
        except Exception as e:
            print 'connect to aws route53 failed, %s' % str(e)
        return

    def change_resource_record_sets_A_IP4(self, action, name, ttl, value):
        if action not in ['CREATE', 'DELETE', 'UPSERT']:
            print 'change_resource_record_sets_A_IP4  action check failed.'
            return False

        if self.route53 and name and ttl and value:
            try:
                ret = self.get_hosted_zone_info(hosted_zone_id = self.hosted_zone_id)
                if ret:
                    suffix = ret['HostedZone']['Name'][:-1]
                else:
                    print 'change_resource_record_sets_A_IP4  get suffix hosted_zone_id[%s] failed.' % self.hosted_zone_id
                    return False

                response = self.route53.change_resource_record_sets(
                    HostedZoneId = self.hosted_zone_id,
                    ChangeBatch={
                        'Comment': name + '.' + suffix,
                        'Changes': [
                            {
                                'Action': action,
                                'ResourceRecordSet': {
                                    'Name': name + '.' + suffix,
                                    'Type': 'A',
                                    'TTL': ttl,
                                    'ResourceRecords': [
                                        {
                                            'Value': value
                                        },
                                    ]
                                }
                            }
                        ]
                    }
                )
            except Exception as e:
                print 'change_resource_record_sets_A_IP4 aws route53 name[%s] action[%s] host_zone_id[%s] failed, %s' % (name, action, self.hosted_zone_id, str(e))
                return False
            return self.route53.get_change(Id=response['ChangeInfo']['Id'])
        else:
            print 'change_resource_record_sets_A_IP4 params error.'
            return False

    def change_resource_record_sets_CNAME_ELB(self, action, name, ttl, value):
        if action not in ['CREATE', 'DELETE', 'UPSERT']:
            print 'change_resource_record_sets_CNAME_ELB  action check failed.'
            return False

        if self.route53 and name and ttl and value:
            try:
                ret = self.get_hosted_zone_info(hosted_zone_id = self.hosted_zone_id)
                if ret:
                    suffix = ret['HostedZone']['Name'][:-1]
                else:
                    print 'change_resource_record_sets_CNAME_ELB  get suffix hosted_zone_id[%s] failed.' % self.hosted_zone_id
                    return False

                response = self.route53.change_resource_record_sets(
                    HostedZoneId = self.hosted_zone_id,
                    ChangeBatch={
                        'Comment': name + '.' + suffix,
                        'Changes': [
                            {
                                'Action': action,
                                'ResourceRecordSet': {
                                    'Name': name + '.' + suffix,
                                    'Type': 'CNAME',
                                    'TTL': ttl,
                                    'ResourceRecords': [
                                        {
                                            'Value': value
                                        },
                                    ]
                                }
                            }
                        ]
                    }
                )
            except Exception as e:
                print 'change_resource_record_sets_CNAME_ELB aws route53 name[%s] action[%s] host_zone_id[%s] failed, %s' % (name, action, self.hosted_zone_id, str(e))
                return False
            return self.route53.get_change(Id=response['ChangeInfo']['Id'])
        else:
            print 'change_resource_record_sets_CNAME_ELB params error.'
            return False
            
    def change_resource_record_sets_A_ELB(self, action, name, elb_hosted_zone_id, elb_dns_name, alias_target_health = False):
        if action not in ['CREATE', 'DELETE', 'UPSERT']:
            print 'change_resource_record_sets_A_ELB  action check failed.'
            return False

        if self.route53 and name and elb_hosted_zone_id and elb_dns_name:
            try:
                ret = self.get_hosted_zone_info(hosted_zone_id = self.hosted_zone_id)
                if ret:
                    suffix = ret['HostedZone']['Name'][:-1]
                else:
                    print 'change_resource_record_sets_A_IP4  get suffix hosted_zone_id[%s] failed.' % self.hosted_zone_id
                    return False

                response = self.route53.change_resource_record_sets(
                    HostedZoneId = self.hosted_zone_id,
                    ChangeBatch={
                        'Comment': name + '.' + suffix,
                        'Changes': [
                            {
                                'Action': action,
                                'ResourceRecordSet': {
                                    'Name': name + '.' + suffix,
                                    'Type': 'A',
                                    'AliasTarget': {
                                        'HostedZoneId': elb_hosted_zone_id,
                                        'DNSName': elb_dns_name,
                                        'EvaluateTargetHealth': alias_target_health
                                    }
                                }
                            }
                        ]
                    }
                )
            except Exception as e:
                print 'change_resource_record_sets_A_ELB aws route53 name[%s] action[%s] host_zone_id[%s] elb_hosted_zone_id[%s] elb_dns_name[%s] failed, %s' % (name, action, self.hosted_zone_id, elb_hosted_zone_id, elb_dns_name, str(e))
                return False
            return self.route53.get_change(Id=response['ChangeInfo']['Id'])
        else:
            print 'change_resource_record_sets_A_ELB params error.'
            return False

    def get_change_resource_record_sets_status(self, change_info_id):
        #get_change response:
        #{
        #    u'ChangeInfo': {
        #        u'Status': 'PENDING',
        #        u'Comment': 'us5.seng.com',
        #        u'SubmittedAt': datetime.datetime(2018,
        #        1,
        #        10,
        #        7,
        #        34,
        #        11,
        #        524000,
        #        tzinfo=tzutc()),
        #        u'Id': '/change/C1N7IXYZ40ZNH8'
        #    },
        #    'ResponseMetadata': {
        #        'RetryAttempts': 0,
        #        'HTTPStatusCode': 200,
        #        'RequestId': 'a9b98c98-f5d8-11e7-821c-3dabaa43c2a5',
        #        'HTTPHeaders': {
        #            'x-amzn-requestid': 'a9b98c98-f5d8-11e7-821c-3dabaa43c2a5',
        #            'date': 'Wed,
        #            10Jan201807: 34: 16GMT',
        #            'content-length': '285',
        #            'content-type': 'text/xml'
        #        }
        #    }
        #}

        if not change_info_id:
            print 'get_change_resource_record_sets_status  change_info_id check failed.'
            return False

        if self.route53:
            return self.route53.get_change(Id = change_info_id)
        else:
            print 'get_change_resource_record_sets_status params error.'
            return False

    def get_hosted_zone_info(self, hosted_zone_id):
        #get_hosted_zone response:
        #{
        #    u'HostedZone': {
        #        u'ResourceRecordSetCount': 4,
        #        u'CallerReference': 'D5270453-2899-E9B4-9E1D-8748E1FD3787',
        #        u'Config': {
        #            u'Comment': 'seng',
        #            u'PrivateZone': False
        #        },
        #        u'Id': '/hostedzone/Z38ZSB44',
        #        u'Name': 'seng.com.'
        #    },
        #    'ResponseMetadata': {
        #        'RetryAttempts': 0,
        #        'HTTPStatusCode': 200,
        #        'RequestId': '4374f28a-f763-11e7-b62c-0333da58203e',
        #        'HTTPHeaders': {
        #            'x-amzn-requestid': '4374f28a-f763-11e7-b62c-0333da58203e',
        #            'date': 'Fri,
        #            12Jan201806: 38: 55GMT',
        #            'content-length': '657',
        #            'content-type': 'text/xml'
        #        }
        #    },
        #    u'DelegationSet': {
        #        u'NameServers': [
        #            'ns-1004.awsdns-61.net',
        #            'ns-1193.awsdns-21.org',
        #            'ns-1824.awsdns-36.co.uk',
        #            'ns-114.awsdns-14.com'
        #        ]
        #    }
        #}

        if not hosted_zone_id:
            print 'get_hosted_zone_info hosted_zone_id check failed.'
            return False

        if self.route53:
            return self.route53.get_hosted_zone(Id = hosted_zone_id)
        else:
            print 'get_hosted_zone_info params error.'
            return False

class HandlerECS(object):
    def __init__(self, region, access_key_id, access_key_value, LOG):
        self.region = region
        self.access_key_id = access_key_id
        self.access_key_value = access_key_value
        self.LOG = LOG
        self.ecs = None

    def connect(self):
        if self.ecs:
            return True
        try:
            #print self.region,self.access_key_id,self.access_key_value
            self.ecs = boto3.client('ecs', region_name = self.region, aws_access_key_id = self.access_key_id, aws_secret_access_key = self.access_key_value)
        except Exception as e:
            self.LOG.error('connect to aws ecs failed, %s' % str(e))
            return False
        self.LOG.info('connect to aws ecs succ.')
        return True

#cluster
    def create_cluster(self, cluster_name):
        if not cluster_name:
            self.LOG.error('create_cluster params check error.')
            return False
        
        if self.ecs:
           try:
               response = self.ecs.create_cluster( clusterName = cluster_name)
           except Exception as e:
               self.LOG.error('create_cluster aws ecs cluster failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('create_cluster cluster_name[%s] succ.' % cluster_name)
               return response['cluster']['clusterArn']
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False
        else:
           self.LOG.error('create_cluster aws not connect to ecs.')
           return False

    def delete_cluster(self, cluster_name):
        if not cluster_name:
            self.LOG.error('delete_cluster params check error.')
            return False
        
        if self.ecs:
           try:
               response = self.ecs.delete_cluster( cluster = cluster_name)
           except Exception as e:
               self.LOG.error('delete_cluster aws ecs cluster failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('delete_cluster cluster_name[%s] succ.' % cluster_name)
               return response['cluster']['clusterArn']
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False
        else:
           self.LOG.error('delete_cluster aws not connect to ecs.')
           return False

    def describe_cluster(self, cluster_name):
        if not cluster_name:
            self.LOG.error('describe_cluster params check error.')
            return False
        
        if self.ecs:
           try:
               response = self.ecs.describe_clusters( clusters = [cluster_name])
           except Exception as e:
               self.LOG.error('describe_cluster aws ecs cluster failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('describe_cluster cluster_name[%s] succ.' % cluster_name)
               return response['clusters'][0]
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False
        else:
           self.LOG.error('describe_cluster aws not connect to ecs.')
           return False

    def list_clusters_arn(self):
        cluster_arns = []
        next_token = ''
        if self.ecs:
            try:
                while(True):
                    if not next_token:
                        response = self.ecs.list_clusters()
                    else:
                        response = self.ecs.list_clusters(nextToken = next_token)

                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        if len(response['clusterArns']) > 0:
                            cluster_arns.extend(response['clusterArns'])
                        if response.has_key('nextToken'):
                            next_token = response['nextToken']
                        else:
                            break
                    else:
                        self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
                        return False
            except Exception as e:
                self.LOG.error('list_clusters_arn aws ecs cluster exception:%s' % (str(e)))
                return False
            self.LOG.info('list_clusters_arn succ found [%d] rows.' % (len(cluster_arns)))
            return cluster_arns
        else:
            self.LOG.error('list_clusters_arn error: aws not connect to ecs.')
            return False

    def get_cluster_arn_by_name(self, cluster_name):
        if not cluster_name:
            self.LOG.info('get_cluster_arn_by_name  cluster_name check failed.')
            return False
            
        if self.ecs:
           cluster_arns = self.list_clusters_arn()
           self.LOG.info('get_cluster_arn_by_name found [%d] rows cluster' % len(cluster_arns))

           if len(cluster_arns) > 0:
               for item in cluster_arns:
                   self.LOG.info('get_cluster_arn_by_name arn[%s] start.' % (item))
                   if item.split('/')[1] == cluster_name:
                       self.LOG.info('get_cluster_arn_by_name arn[%s] cluster_name[%s] succ.' % (item, cluster_name))
                       return item
                   self.LOG.info('get_cluster_arn_by_name arn[%s] end.' % (item))
           else:
               self.LOG.error('get_cluster_arn_by_name not found clusters, please retry.')
               return False
        else:
           self.LOG.error('get_cluster_arn_by_name error: aws not connect to ecs.')
           return False

#service
    def create_service(self, **kwargs):
        pass
    def delete_service(self, cluster_name, service_name):
        pass
    def list_services_arn(self, cluster_name):
        service_arns = []
        next_token = ''
        if self.ecs:
            try:
                while(True):
                    if not next_token:
                        response = self.ecs.list_services(cluster = cluster_name)
                    else:
                        response = self.ecs.list_services(cluster = cluster_name, nextToken = next_token)

                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        if len(response['serviceArns']) > 0:
                            service_arns.extend(response['serviceArns'])
                        if response.has_key('nextToken'):
                            next_token = response['nextToken']
                        else:
                            break
                    else:
                        self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
                        return False
            except Exception as e:
                self.LOG.error('list_services_arn aws ecs service exception:%s' % (str(e)))
                return False
            self.LOG.info('list_services_arn succ found [%d] rows.' % (len(service_arns)))
            return service_arns
        else:
            self.LOG.error('list_services_arn error: aws not connect to ecs.')
            return False

    def desc_service_by_name(self, cluster_name, service_name):
        if not cluster_name or not service_name:
            self.LOG.error('desc_service_by_name service_arn check failed.')
            return False

        if self.ecs:
           try:
               response = self.ecs.describe_services(cluster = cluster_name, services=[service_name])
           except Exception as e:
               self.LOG.error('desc_service_by_name aws ecs service exception:%s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('desc_service_by_name cluster_name[%s] service_name[%s] succ.' % (cluster_name, service_name))
               return response['services'][0]
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False
        else:
           self.LOG.warning('desc_service_by_name not found client, retry.')
           self.connect()
           self.LOG.info('desc_service_by_name retry succ.')
           
           try:
               response = self.ecs.describe_services(cluster = cluster_name, services=[service_name])
           except Exception as e:
               self.LOG.error('desc_service_by_name aws ecs service exception:%s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('desc_service_by_name cluster_name[%s] service_name[%s] succ.' % (cluster_name, service_name))
               return response['services'][0]
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False

    def get_service_arn_by_name(self, cluster_name, service_name):
        if not cluster_name or not service_name or not self.ecs:
            self.LOG.error('get_service_arn_by_name params check failed.')
            return False
        service_arns = self.list_services_arn(cluster_name = cluster_name)
        
        service_arn = None
        for item in service_arns:
            if service_name == item.split('/')[1]:
                service_arn = item
                break
        if service_arn:
            self.LOG.info('get_service_arn_by_name found service_name[%s] service_arn[%s] cluster_name[%s] succ.' % (service_name, service_arn, cluster_name))
            return service_arn
        else:
            self.LOG.error('get_service_arn_by_name found service_name[%s] cluster_name[%s] error, please retry.' % (service_name, cluster_name))
            return False

    def get_service_taskdefinition_arn_by_name(self, cluster_name, service_name):
        if not cluster_name or not service_name or not self.ecs:
            self.LOG.error('get_service_taskdefinition_arn_by_name params check failed.')
            return False
        service_info = self.desc_service_by_name(cluster_name = cluster_name, service_name = service_name)
        
        task_definition_arn = None
        if service_info:
            task_definition_arn = service_info['taskDefinition']
            self.LOG.info('get_service_taskdefinition_arn_by_name found service_name[%s] cluster_name[%s] task_definition_arn[%s] succ.' % (service_name, cluster_name, task_definition_arn))
        else:
            self.LOG.error('get_service_taskdefinition_arn_by_name found service_name[%s] cluster_name[%s] task_definition_arn[%s] error.' % (service_name, cluster_name, task_definition_arn))
        return task_definition_arn

    def update_service(self, cluster_arn, service_name, task_definition_arn, desired_count, deploy_min_healthy_percent, deploy_max_percent):
        if not cluster_arn or not service_name or not task_definition_arn or not desired_count or not deploy_min_healthy_percent or not deploy_max_percent:
            self.LOG.error('update_service params check error.')
            return False

        if self.ecs:
           try:
               response = self.ecs.update_service(
                   cluster = cluster_arn,
                   service = service_name,
                   desiredCount = int(desired_count),
                   taskDefinition = task_definition_arn,
                   deploymentConfiguration = {
                       'maximumPercent': int(deploy_max_percent),
                       'minimumHealthyPercent': int(deploy_min_healthy_percent)
                   }
               )
           except Exception as e:
               self.LOG.error('update_service aws ecs task_definitions failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('update_service cluster_arn[%s] service[%s] task_definition_arn[%s] desired_count[%s] deploy_min_healthy_percent[%s] deploy_max_percent[%s] succ.' %
               (cluster_arn, service_name, task_definition_arn, desired_count, deploy_min_healthy_percent, deploy_max_percent))
               return response['service']
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False
        else:
           self.LOG.warning('update_service not found client, retry.')
           self.connect()
           self.LOG.info('update_service retry succ.')
           
           try:
               response = self.ecs.update_service(
                   cluster = cluster_arn,
                   service = service_name,
                   desiredCount = desired_count,
                   taskDefinition = task_definition_arn,
                   deploymentConfiguration = {
                       'maximumPercent': int(deploy_max_percent),
                       'minimumHealthyPercent': int(deploy_min_healthy_percent)
                   }
               )
           except Exception as e:
               self.LOG.error('update_service aws ecs task_definitions failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('update_service cluster_arn[%s] service[%s] task_definition_arn[%s] desired_count[%s] deploy_min_healthy_percent[%s] deploy_max_percent[%s] succ.' %
               (cluster_arn, service_name, task_definition_arn, desired_count, deploy_min_healthy_percent, deploy_max_percent))
               return response['service']
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False


#task definition
    def list_task_definitions_arn(self, family_prefix, status = 'ACTIVE', sort = 'ASC'):
        if not family_prefix:
            self.LOG.error('list_task_definitions_arn params error, please retry.')
            return False

        task_definition_arns = []
        next_token = ''
        if self.ecs:
            try:
                while(True):
                    if not next_token:
                        response = self.ecs.list_task_definitions(familyPrefix = family_prefix, status = status, sort = sort )
                    else:
                        response = self.ecs.list_task_definitions( familyPrefix = family_prefix, status = status, sort = sort, nextToken = next_token )

                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        if len(response['taskDefinitionArns']) > 0:
                            task_definition_arns.extend(response['taskDefinitionArns'])
                        if response.has_key('nextToken'):
                            next_token = response['nextToken']
                        else:
                            break
                    else:
                        self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
                        return False
            except Exception as e:
                self.LOG.info('list_task_definitions_arn aws ecs task_definition exception:%s' % (str(e)))
                return False
            self.LOG.info('list_task_definitions_arn succ found [%d] rows.' % (len(task_definition_arns)))
            return task_definition_arns
        else:
            self.LOG.error('list_task_definitions_arn error: aws not connect to ecs.')
            return False

    def get_latest_task_definitions_by_name(self, family_prefix):
        if not family_prefix or not self.ecs:
            self.LOG.error('get_latest_task_definitions_by_name params check failed.')
            return False
        latest_task_definition = self.list_task_definitions_arn(family_prefix, status = 'ACTIVE', sort = 'DESC')[0][0] 
        self.LOG.info('get_latest_task_definitions_by_name found arn[%s] family_prefix[%s] succ.' % (latest_task_definition, family_prefix))
        return latest_task_definition
        
    def desc_task_definitions_by_arn(self, task_definition_arn):
        if not task_definition_arn:
            self.LOG.error('desc_task_definitions_by_arn task_definition_arn check failed.')
            return False
            
        if self.ecs:
           try:
               response = self.ecs.describe_task_definition(taskDefinition = task_definition_arn)
           except Exception as e:
               self.LOG.error('desc_task_definitions_by_arn aws ecs task_definitions failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('desc_task_definitions_by_arn arn[%s] succ.' % task_definition_arn)
               return response['taskDefinition']
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False
        else:
           self.LOG.warning('desc_task_definitions_by_arn not found client, retry.')
           self.connect()
           self.LOG.info('desc_task_definitions_by_arn retry succ.')
           
           try:
               response = self.ecs.describe_task_definition(taskDefinition = task_definition_arn)
           except Exception as e:
               self.LOG.error('desc_task_definitions_by_arn aws ecs task_definitions failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('desc_task_definitions_by_arn arn[%s] succ.' % task_definition_arn)
               return response['taskDefinition']
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False

    def register_task_definition(self, family, networkMode, containerDefinitions, requiresCompatibilities, taskRoleArn, volumes = [], placementConstraints = [], executionRoleArn = None, memory = None):
        if not family or not networkMode or not containerDefinitions or not requiresCompatibilities:
            self.LOG.error('register_task_definition params check error.')
            return False
        
        if self.ecs:
           try:
               response = self.ecs.register_task_definition(
                   family = family,
                   taskRoleArn = taskRoleArn,
                   networkMode = networkMode,
                   containerDefinitions = containerDefinitions,
                   volumes = volumes,
                   placementConstraints = placementConstraints,
                   #executionRoleArn = executionRoleArn,
                   #requiresCompatibilities = requiresCompatibilities,
                   #memory = memory
               )
           except Exception as e:
               self.LOG.error('register_task_definition aws ecs task_definitions failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('register_task_definition family[%s] succ.' % family)
               return response['taskDefinition']['taskDefinitionArn']
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False
        else:
           self.LOG.error('register_task_definition not found client, retry.')
           self.connect()
           self.LOG.info('register_task_definition retry succ.')

           try:
               response = self.ecs.register_task_definition(
                   family = family,
                   taskRoleArn = taskRoleArn,
                   networkMode = networkMode,
                   containerDefinitions = containerDefinitions,
                   volumes = volumes,
                   placementConstraints = placementConstraints,
                   #executionRoleArn = executionRoleArn,
                   #requiresCompatibilities = requiresCompatibilities,
                   #memory = memory
               )
           except Exception as e:
               self.LOG.error('register_task_definition aws ecs task_definitions failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('register_task_definition family[%s] succ.' % family)
               return response['taskDefinition']['taskDefinitionArn']
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False

    def deregister_task_definition(self, task_definition_arn):
        if not task_definition_arn:
            self.LOG.error('deregister_task_definition task_definition_arn check failed.')
            return False
            
        if self.ecs:
           try:
               task_definition = self.ecs.deregister_task_definition(taskDefinition = task_definition_arn)
           except Exception as e:
               self.LOG.error('deregister_task_definition aws ecs task_definitions failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('deregister_task_definition arn[%s] succ.' % task_definition_arn)
               return response['taskDefinition']
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False
        else:
           self.LOG.error('deregister_task_definition not found client, retry.')
           self.connect()
           self.LOG.info('deregister_task_definition retry succ.')
           
           try:
               task_definition = self.ecs.deregister_task_definition(taskDefinition = task_definition_arn)
           except Exception as e:
               self.LOG.error('deregister_task_definition aws ecs task_definitions failed, %s' % (str(e)))
               return False
           if response['ResponseMetadata']['HTTPStatusCode'] == 200:
               self.LOG.info('deregister_task_definition arn[%s] succ.' % task_definition_arn)
               return response['taskDefinition']
           else:
               self.LOG.error('aws response error code is [%d]' % response['ResponseMetadata']['HTTPStatusCode'])
               return False

#task
    def start_task(self, **kwargs):
        pass
    def stop_task(self, cluster_arn, task_arn, reason):
        pass

#container

#ecs



#if __name__ == '__main__':
    #route53.connect()
    #ret = route53.change_resource_record_sets_A_IP4(action = 'CREATE', name = 'us5', ttl = 300, value = '10.0.0.1')
    #ret = route53.change_resource_record_sets_A_IP4(action = 'DELETE', name = 'us5', ttl = 300, value = '10.0.0.2')

    #ret = route53.change_resource_record_sets_CNAME_ELB(action = 'CREATE', name = 'us5', ttl = 300, value = 'elb-us.us-west-2.elb.amazonaws.com')
    #ret = route53.change_resource_record_sets_CNAME_ELB(action = 'DELETE', name = 'us5', ttl = 300, value = 'elb-us.us-west-2.elb.amazonaws.com')

    #ret = route53.change_resource_record_sets_A_ELB(action = 'CREATE', name = 'us5', elb_hosted_zone_id = 'Z1H1FL5HABSF5', elb_dns_name = 'elb-us-west-2.elb.amazonaws.com', alias_target_health = False)
    #ret = route53.change_resource_record_sets_A_ELB(action = 'DELETE', name = 'us5', elb_hosted_zone_id = 'Z1H1FL5HABSF5', elb_dns_name = 'elb-us.us-west-2.elb.amazonaws.com', alias_target_health = False)

    #status = route53.get_change_resource_record_sets_status(change_info_id = ret['ChangeInfo']['Id'])
    #status = route53.get_change_resource_record_sets_status(change_info_id = '/change/CBP3WMHPPI')
    #print '----------------------------'
    #print status
