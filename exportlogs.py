import boto3
import time
import os

currentTime = time.time()

#CloudWatch Logs may not be available for export for up to 12 hours so logToTime is set to 12 hours ago and logFromTime 36 hours
logFromTime=int((currentTime - (currentTime % 3600) - 129600) * 1000)
logToTime=int((currentTime - (currentTime % 3600) - 43200) * 1000)

#Setup client
client = boto3.client('logs',region_name=os.environ['LOGS_REGION'])

#Get log groups
logGroups = client.describe_log_groups()

resultMessage=""

#Iterate through log groups
for logGroup in logGroups["logGroups"]:
    print("%s: %s" % (time.strftime('%Y-%d-%m %H:%M:%S'),logGroup["logGroupName"]))
    resultMessage+="%s: %s\n" % (time.strftime('%Y-%d-%m %H:%M:%S'),logGroup["logGroupName"])
    exportTaskResponse = client.create_export_task(
        taskName=logGroup["logGroupName"],
        logGroupName=logGroup["logGroupName"],
        fromTime=logFromTime,
        to=logToTime,
        destination=os.environ['LOGS_BUCKET'],
        destinationPrefix='cloudwatchlogs%s/%s'% (logGroup["logGroupName"],time.strftime('%Y-%d-%mT%H.%M.%SZ',  time.gmtime(logFromTime/1000)))
    )

#There is a limit of 1 export running at a time so wait until current export is finshed    
    exportStatus = client.describe_export_tasks(taskId=exportTaskResponse["taskId"])
    print exportStatus["exportTasks"][0]["status"]["code"]
    resultMessage+=exportStatus["exportTasks"][0]["status"]["code"]+'\n'
    while exportStatus["exportTasks"][0]["status"]["code"] != "COMPLETED":
        exportStatus = client.describe_export_tasks(taskId=exportTaskResponse["taskId"])
        time.sleep(10)
        print exportStatus["exportTasks"][0]["status"]["code"]
        resultMessage+=exportStatus["exportTasks"][0]["status"]["code"]+'\n'


#Setup client
snsClient = boto3.client('sns',region_name=os.environ['LOGS_REGION'])

#Send message
response = snsClient.publish(
    TopicArn=os.environ['LOGS_SNS_TOPIC'],
    Message=resultMessage,
    Subject='CloudWatch Logs Export Results'
)



