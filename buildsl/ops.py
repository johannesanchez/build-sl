import json
from unittest import result

import boto3
import logging
import sys
import json
from botocore.config import Config
from datetime import timezone, datetime, timedelta


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

# AWS Clients & waiters
config = Config(retries=dict(max_attempts=10))


def lambda_handler(event, context):
    app = event['queryStringParameters']['app']
    region = event['queryStringParameters']['region']
    env = event['queryStringParameters']['env']
    instance = event['queryStringParameters']['instance']
    action = event['queryStringParameters']['action']

# try:
    # print(event)
    http_method = event['httpMethod']
    if http_method == 'POST':


        if action == 'cleanup_alb':
            arnsBlueTgs = getAlbs(env, instance, region)
            print('final tgs', arnsBlueTgs)
            if arnsBlueTgs[0]['tgs']['green'] != '':
                stacksToDelete = listOldStacks(arnsBlueTgs, env, region)
                print("stacksToDelete: ", stacksToDelete)

                if stacksToDelete != '':
                    if removeGreenFromLB(arnsBlueTgs, env, region):
                        removeGreenStack(stacksToDelete, env, region)
                        arnsBlueTgs = "stack was removed successfully"
                    else:
                        arnsBlueTgs = "stack was not removed"
                else:
                    arnsBlueTgs = "stack is into the timeout_stack rule"
            else:
                arnsBlueTgs = 'No green TG found'


    # except:
    #     return {
    #         'statusCode': 301,
    #         'Reason': 'https://example.com'
    #     }
    elif http_method == 'GET':
        arnsBlueTgs = ''
        if action == 'status':
            arnsBlueTgs = getAlbs(env, instance, region)
        # print("value for get")

    result = arnsBlueTgs
    print(result)
    return {
        "statusCode": 200,
        "body": json.dumps(result)
    }
    
    # return {
    #     "statusCode": 200,
    #     "body": json.dumps({
    #         "blueTGs": arnsBlueTgs,
    #         "stacksToDelete": stacksToDelete,
    #     }),
    # }


def getAlbs(env, instance, region):
    elbv2_client = boto3.client('elbv2', region, config=config)
    """ :type : pyboto3.elasticloadbalancingv2 """
    ListenerArn = ''
    tgs = {}
    matriz = []
    
    lbs = elbv2_client.describe_load_balancers()
    for bluelb in lbs["LoadBalancers"]:
        if (bluelb['Type'] == 'application'):
          if (bluelb['LoadBalancerName'].startswith(env+'-'+instance)):
            listeners=elbv2_client.describe_listeners(LoadBalancerArn=bluelb['LoadBalancerArn'])
            for listener in listeners["Listeners"]:
                alb_listener = listener['ListenerArn']
                # print("THESE ARE the listeners: ", alb_listener)
                tgsAlb = listener["DefaultActions"][0]["ForwardConfig"]["TargetGroups"]
                # tgsAlb = listeners["Listeners"][0]["DefaultActions"][0]["ForwardConfig"]["TargetGroups"]
                # print("tgs associated: ", tgsAlb)
                blue = ''
                green = ''
                for i in tgsAlb:
                    # print("total i: ", i)
                    # print(i['Weight'])
                    # print(list(i.values()))
                    # print("\n")
                    # if list(i.values())[0] == 100:
                    if i["Weight"] == 100:
                        # print("OK BLUE")
                        # blue=list(i.keys())[0]
                        blue=i["TargetGroupArn"]
                    elif i["Weight"] == 0:
                        # print("OK GREEN")
                        # green=list(i.keys())[0]
                        green=i["TargetGroupArn"]
                listen = {"listener": alb_listener}
                # print("FINAL LISTEN: ", listen)
                tgs = {'blue': blue, 'green': green}
                # print("FINAL LISTEN: ", tgs)
                final = {'listener': alb_listener, 'tgs':tgs}
                # print("final_FINAL", final)
                matriz.append(final)
                # print("\n")

    return matriz



def listOldStacks(listeners, env, region):
    cfn_client = boto3.client('cloudformation', region, config=config)
    """ :type : pyboto3.elasticloadbalancingv2 """
    green_stack_name = ''
    # print("tgs on LISTOLDSTACK: ", tgs['green'])

    past = datetime.now() - timedelta(hours=1)
    past_utc = past.astimezone(timezone.utc)
    # print("LISTENERS: ", listeners[0]['tgs'])
    if listeners[0]['tgs']['green'] != '':
        stack = cfn_client.describe_stack_resources(PhysicalResourceId=listeners[0]['tgs']['green'])
        # print("STACK FOUND: ", stack)
        # stack = cfn_client.describe_stack_resources(PhysicalResourceId=tgs[0])
        stack_timestamp_utc = stack['StackResources'][0]['Timestamp']
        
        # when stack out of the rule: alb_tg_expired
        print("stack_timestamp_utc: ", stack_timestamp_utc)
        print("past_utc: ", past_utc)
        if stack_timestamp_utc < past_utc:
            green_stack_name = stack["StackResources"][0]["StackName"]
            # print("green_stack_name: ", green_stack_name)

    return green_stack_name


def removeGreenFromLB(listeners, env, region):
    elbv2_client = boto3.client('elbv2', region, config=config)
    """ :type : pyboto3.elasticloadbalancingv2 """

    # print("LISTENERS: ", listeners)
    for listener in listeners:
        # print("listener: ", listener['listener'])
        # print("GreenTG: ", listener['tgs']['green'])
        # print("\n")
        if listener['tgs']['green'] != '':
            updateListener = elbv2_client.modify_listener(
                DefaultActions=[{'Type': 'forward', 'Order': 1,
                                'ForwardConfig': {'TargetGroups': [{'TargetGroupArn': listener['tgs']['blue'],
                                                                    'Weight': 100}], }, }],
                ListenerArn=listener['listener'])
    # updateListener = ''
    return updateListener


def removeGreenStack(stack, env, region):
    cfn_client = boto3.client('cloudformation', region, config=config)
    """ :type : pyboto3.elasticloadbalancingv2 """

    resultRemoveStack = cfn_client.delete_stack(StackName=stack)
    print("resultRemoveStack", resultRemoveStack)
    return 'Stack Removed'

# CFG_AWS_REGION = sys.argv[1]
# CFG_ENV = sys.argv[2]
# CFG_INSTANCE = sys.argv[3]

# # AWS Clients & waiters
# config = Config(retries=dict(max_attempts=10))

# elbv2_client = boto3.client('elbv2', CFG_AWS_REGION, config=config)
# """ :type : pyboto3.elasticloadbalancingv2 """


# def getAlbs(env, instance):
#     bluelisteners=[]
#     lbs = elbv2_client.describe_load_balancers()
#     for bluelb in lbs["LoadBalancers"]:
#         if (bluelb['Type'] == 'application'):
#           if (bluelb['LoadBalancerName'].startswith(env+'-'+instance)):
#             listeners=elbv2_client.describe_listeners(LoadBalancerArn=bluelb['LoadBalancerArn'])
#             for elements in listeners["Listeners"][0]["DefaultActions"][0]["ForwardConfig"]["TargetGroups"]:
#                 if (elements["Weight"] == 100):
#                   elementblueTG = elements["TargetGroupArn"]
#             bluelisteners.append(elementblueTG)
#     return bluelisteners


# def getBlueInstances(arnsBlueTgs):
#   blueInstances=[]
#   for currentBlueTG in arnsBlueTgs:
#     infoBlueTG=elbv2_client.describe_target_health(TargetGroupArn=currentBlueTG)
#     for instanceId in infoBlueTG["TargetHealthDescriptions"]:
#       blueInstances.append(instanceId["Target"]["Id"])
#   return blueInstances


# arnsBlueTgs=getAlbs(CFG_ENV, CFG_INSTANCE)
# blueinstances=getBlueInstances(arnsBlueTgs)
# print(blueinstances)