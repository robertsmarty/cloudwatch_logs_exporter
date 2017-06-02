### What is this repository for? ###

Provides configuration and instructions to setup a daily export of CloudWatch Logs to an S3 bucket and send a notification to an SNS topic.

### How do I get set up? ###

Follow these steps to get setup...

* Configure a S3 bucket and bucket policy to allow CloudWatch to export logs
* Configure an IAM policy which allows access to export logs, get export script from S3 and sent notifications to an SNS topic
* Configure an IAM Role which can be applied to EC2 instances which will run the export script
* Configure an EC2 launch configuration with userdata which will bootstrap the instance
* Configure an auto scaling group with a schedule to launch a single EC2 instance once a day to perform the export
* Upload exportlogs.py script to the bucket

### S3 Bucket Configuration ###

Copy the exportlogs.py script to the S3 bucket.

The following link provides detail regarding how to configure S3 permissions to receive logs from CloudWatch Logs exports...

http://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/S3ExportTasks.html

The following bucket policy should be applied...

```
{
    "Version": "2008-10-17",
    "Id": "Policy1335892530063",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "logs.[region].amazonaws.com"
            },
            "Action": "s3:GetBucketAcl",
            "Resource": "arn:aws:s3:::[bucket]"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "logs.[region].amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::[bucket]/*",
            "Condition": {
                "StringEquals": {
                    "s3:x-amz-acl": "bucket-owner-full-control"
                }
            }
        }
    ]
}
```
### IAM Policy ###

Create a new IAM Policy "AllowCloudWatchLogsExport" with the following configuration...

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sns:Publish",
            "Resource": "arn:aws:sns:[region]:[account]:[topic]"
        },
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": [
                "arn:aws:s3:::[bucket]/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateExportTask",
                "logs:DescribeExportTasks",
                "logs:DescribeLogGroups"
            ],
            "Resource": "arn:aws:logs:[region]:*:*"
        }
    ]
}
```

### IAM Role ###

Create a new IAM Role "aws-ec2-cloudwatchlogs-export" specifying that it is an Amazon EC2 role and use the "AllowCloudWatchLogsExport" policy.

### Launch Configuration ###

Create a launch configuration "CloudWatchLogsExport-vX.X" using...

* Amazon Linux
* t2.micro
* "aws-ec2-cloudwatchlogs-export" IAM role
* No public IP enabled
* Default storage
* Security group with outbound internet access
* No SSH keys

Userdata must contain the following...

```
#!/bin/bash
export LOGS_REGION=[region]
export LOGS_SNS_TOPIC=[topic arn]
export LOGS_BUCKET=[bucket]
sudo pip install boto3
aws s3 cp s3://[bucket]/exportlogs.py .
python exportlogs.py
```

### Auto Scaling Group Configuration ###

Create an auto scaling group "CloudWatchLogsExport" using the "CloudWatchLogsExport-vX.X" launch configuration, with 0 instances, utilising a private subnet and no scaling policy.

Once created, configure 2 Scheduled Actions "StartExport" and "EndExport". "StartExport" increases instances in the group to 1 and "EndExport" decreases to 0. Initially, set end time to 50 minutes past start time as EC2 charges by the hour. This will need to be tuned as the export could take longer than an hour.

### Testing ###

You can test by manually changing the number of members in the auto scaling group.

If you subscribe an email address to the SNS topic you should receive an email with a subject of "CloudWatch Logs Export Results" and will have a message which will look something like this...

```
2017-01-06 12:02:38: /aws/lambda/aws-python-dev-location
PENDING
PENDING
COMPLETED
2017-01-06 12:02:59: /aws/lambda/position-dev-hello
PENDING
PENDING
COMPLETED
```

### CloudFormatioon ###

Don't want to do things manually? Then use the CloudFormation script in this repo!
