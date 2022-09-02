# build-sl
Build Serverless

# Way to deploy lambda
1. sam build
2. sam package
3. sam deploy --guided

# Test locally
sam local start-api

* Local request:
http://127.0.0.1:3000/status?personId=5