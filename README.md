# build-sl
Build Serverless

# Way to deploy lambda
1. sam build
2. sam package
3. sam deploy --guided

# Test locally
sam local start-api
sam local start-api --skip-pull-image

* Local request:
http://127.0.0.1:3000/status?personId=5

GET
http://127.0.0.1:3000/ops?app=ef-decision&region=us-east-1&env=stage&instance=3&action=status

POST
http://127.0.0.1:3000/ops?app=ef-decision&region=us-east-1&env=stage&instance=3&action=cleanup_alb


AWS SAM Policies:
https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-policy-templates.html

Notes:
-  Eventbridge push the event to lambda


Visual Studio Code Extensions
- Thunder Client
- Serverless Console


<!-- EventBridge
Managed - Event Pattern
{
  "source": ["aws.health"],
  "detail-type": ["AWS Health Event"],
  "detail": {
    "service": ["EC2"],
    "eventTypeCategory": ["scheduledChange"]
  }
} -->