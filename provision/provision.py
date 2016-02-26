import boto3
import base64
import time
import sys
from datetime import datetime

ec2 = boto3.client('ec2')


def _prices(az):
    a = ec2.describe_spot_price_history(StartTime=datetime(2016, 1, 1), InstanceTypes=['g2.2xlarge'],
                                        AvailabilityZone=az, ProductDescriptions=['Linux/UNIX'])
    return sorted(a['SpotPriceHistory'], key=lambda s: s['Timestamp'])


def prices():
    return zip(_prices('us-east-1a'), _prices('us-east-1b'), _prices('us-east-1c'), _prices('us-east-1e'))


def user_data(**kargs):
        return """#!/bin/bash
        cd /usr/local/cuda/samples/1_Utilities/deviceQuery && make && ./deviceQuery

        cd /home/{user_name}

        sudo su {user_name} -c "mkdir -p /home/{user_name}/.aws"

        sudo su {user_name} -c "aws s3 sync s3://dqn-setup /home/{user_name}/dqn-setup"


        sudo su {user_name} -c "git clone https://github.com/maciejjaskowski/{project_name}.git"
        sudo su {user_name} -c "git reset --hard {sha1}"
        sudo su {user_name} -c "mkdir -p /home/{user_name}/{project_name}/weights"
        sudo su {user_name} -c "mkdir -p /home/{user_name}/{project_name}/logs"
        sudo su {user_name} -c "cp /home/{user_name}/dqn-setup/space_invaders.bin /home/{user_name}/{project_name}/"

        sudo su {user_name} -c "aws s3 sync s3://{exp_name}/weights /home/{user_name}/{project_name}/weights"

        aws s3 mb s3://{exp_name}



        export PATH=/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:; export LD_LIBRARY_PATH=/usr/local/cuda/lib64;  echo $PATH > /home/{user_name}/path.log; echo $LD_LIBRARY_PATH /home/{user_name}/ld.log; cd /home/{user_name}/{project_name} && THEANO_FLAGS='floatX=float32,[mode]=FAST_RUN,fastmath=True,root=/usr/local/cuda,device=gpu,lib.cnmem=0.9' python ex1.py 2> log.err | multilog t s4000000 ./logs &

        watch -n 60 "sudo su {user_name} -c 'aws s3 sync /home/{user_name}/{project_name}/weights s3://{exp_name}/weights' && sudo su {user_name} -c 'aws s3 sync /home/{user_name}/{project_name}/logs s3://{exp_name}/logs' && echo `date` >> /home/{user_name}/last_sync" &
        """.format(**kargs)


def provision(client_token, user_data, availability_zone, spot_price):

    result = ec2.request_spot_instances(DryRun=False,
                                        ClientToken=client_token,
                                        SpotPrice=spot_price,
                                        InstanceCount=1,
                                        AvailabilityZoneGroup=availability_zone,
                                        Type='persistent',
                                        LaunchSpecification={
                                            'ImageId': 'ami-bdd2efd7',
                                            'KeyName': 'gpu-east',
                                            'InstanceType': 'g2.2xlarge',
                                            'Placement': {
                                                'AvailabilityZone': availability_zone
                                            },
                                            'BlockDeviceMappings': [{
                                                'DeviceName': '/dev/sda1',
                                                'Ebs': {
                                                    'VolumeSize': 25,
                                                    'DeleteOnTermination': True,
                                                    'VolumeType': 'standard',
                                                    'Encrypted': True
                                                }
                                            }],
                                            'IamInstanceProfile': {
                                                'Name': 's3'
                                            },
                                            'EbsOptimized': False,
                                            'Monitoring': {
                                                'Enabled': True
                                            },
                                            'UserData': base64.b64encode(user_data.encode("ascii")).decode('ascii'),
                                            'SecurityGroupIds': ['sg-ab1236d2'],

                                        })

    req_id = result['SpotInstanceRequests'][0]['SpotInstanceRequestId']

    print("")
    instance_description = None
    public_dns_name = ''

    while True:
        instance = ec2.describe_spot_instance_requests(SpotInstanceRequestIds=[req_id])['SpotInstanceRequests'][0]
        sys.stdout.write(str(datetime.now().time()) + " " + instance['Status']['Message'] + '\r')
        sys.stdout.flush()

        if 'Fault' in instance.keys():
            return {
                'status': instance['Status'],
                'instance': instance
            }

        if 'InstanceId' in instance.keys() and public_dns_name != '':
            instance_description = ec2.describe_instances(InstanceIds=[instance['InstanceId']])
            public_dns_name = instance_description['Reservations'][0]['Instances'][0]['PublicDnsName']
            break

        time.sleep(1)

    return {
        'status': instance['Status'],
        'instance': instance,
        'instance_description': instance_description,
        'public_dns_name': public_dns_name
    }


# def attach_volume(instance):
#     while True:
#         try:
#             ec2.attach_volume(
#                 DryRun=False,
#                 VolumeId='vol-32b4d7ed',
#                 InstanceId=instance['InstanceId'],
#                 Device='/dev/xvdf')
#             time.sleep(1)
#         except:
#             import traceback
#             traceback.print_exc()
#             print(datetime.now().time(), "Not ready yet.")
#             import sys
#             print(sys.exc_info()[2])
#         else:
#             break


def main():

    project_name = "deep-q-learning"
    sha1 = "8031e777"

    availability_zone = 'us-east-1a'
    spot_price = '0.01'

    client_token = sys.argv[1]
    user_script = user_data(exp_name=client_token, sha1=sha1, user_name="ubuntu", project_name=project_name)

    print """
    project_name: {project_name}
    sha1: {sha1}

    availability_zone: {availability_zone}
    spot_price: {spot_price}

    client_token: {client_token}
    user_script:

    {user_script}

    """.format(project_name=project_name, sha1=sha1,
               client_token=client_token, user_script=user_script,
               spot_price=spot_price, availability_zone=availability_zone)

    instance = provision(client_token=client_token, availability_zone=availability_zone,
                         spot_price=spot_price, user_data=user_script)

    print(instance)
    print("public_dns_name: ", instance['public_dns_name'])

    with open('instance.dns', 'w') as f:
        f.write(str(instance['public_dns_name']))

if __name__ == "__main__":
    main()



