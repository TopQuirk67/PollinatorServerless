# PollinatorServerless

## TODOs
- push to master
- git squash
- fix the page too big problem
- Convert 2 API accounts to paid
- tear down everything and follow these instructions from scratch
- reduce logging in lambdas
- document how to use the twilio updater
- include an architecture diagram
- make sure you have README instructions without sam build/deploy and also has all the environmental definitions you need
- tear down everything and pull to a new directory from origin and follow the README for installation to make sure it's all there in order


### Set the environment variable for the S3 bucket name

We need to set environmental variable for Twilio account information.  I have done these in the .zshrc file.  These variables are:

```
$TWILIOPHONENUMBER
$TWILIOPHONENUMBERSID
$TWILIOACCTSID
$TWILIOAUTHTOKEN
$RAPIDAPI_ENDPOINT
$RAPIDAPI_HOST
$RAPIDAPI_KEY
```

#TODO: git squash this commit and delete the dev_tesseract branch locally
The commits to squash is:
master f347594fd8f32edd44f4176cebcc98bcffa41175
dev_tesseract f347594fd8f32edd44f4176cebcc98bcffa41175

We need environmental variables for two S3 buckets:
$POLLINATORARTIFACTBUCKET: this is where the Lambda layers will go
$POLLINATOROUTPUTBUCKET: this is where temporary files such as output PDF will go.  It has public access so that Twilio can grab the PDF

```
export POLLINATOROUTPUTBUCKET=pollinatorserverless
export POLLINATORARTIFACTBUCKET=pollinatorserverlessartifact
```

## IAM

Prior to any cloudformation stack creation, you should always check that the CFT lints:

```
cfn-lint pollinator_serverless_cft.yaml
```

### Create Buckets first to upload code to.
```
aws s3api create-bucket --bucket $POLLINATORARTIFACTBUCKET  \
--region us-west-2 \
--create-bucket-configuration LocationConstraint=us-west-2 \
--profile g_h_scrabble
```

### Create output bucket with 1 hr lifecycle policy.
```
aws s3api create-bucket --bucket $POLLINATOROUTPUTBUCKET \
--region us-west-2 \
--create-bucket-configuration LocationConstraint=us-west-2 \
--profile g_h_scrabble

aws s3api put-bucket-lifecycle-configuration --bucket $POLLINATOROUTPUTBUCKET --lifecycle-configuration file://lifecyclepolicy.json --profile g_h_scrabble
```

The `lifecyclepolicy.json` policy is:

```
{
  "Rules": [
    {
      "ID": "DeleteAfterOneHour",
      "Prefix": "",
      "Status": "Enabled",
      "Expiration": {
        "Days": 1
      }
    }
  ]
}
```

Here is the json to make the bucket public:

`public_bucket.json` 

(note that we had to put the bucket name in line not using the environmental variable so if you have changed the name of the output bucket you will need to change it in this policy under "Resource"!)

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::pollinatorserverless/*"  
    }
  ]
}
```

```
aws s3api put-public-access-block --bucket "$POLLINATOROUTPUTBUCKET" --public-access-block-configuration 'BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false'
aws s3api put-bucket-policy --bucket $POLLINATOROUTPUTBUCKET --policy file://public_bucket.json --profile g_h_scrabble 
```
# Create layers for Lambda dependencies 

```
cd lambda_functions
mkdir -p lambda_layer/webhook/python
mkdir -p lambda_layer/ocr/python
mkdir -p lambda_layer/flaskapp/python
mkdir -p lambda_layer/html-to-image/python
python3.9 -m pip install requests twilio boto3 -t lambda_layer/webhook/python
python3.9 -m pip install boto3 -t lambda_layer/ocr/python
python3.9 -m pip install flask==2.0.3 werkzeug==2.0.3 flask_lambda requests beautifulsoup4 pytz -t lambda_layer/flaskapp/python
python3.9 -m pip install requests -t lambda_layer/html-to-image/python
cd lambda_layer/html-to-image
zip -r webhook.zip python
aws s3 cp webhook.zip s3://$POLLINATORARTIFACTBUCKET/lambda_layers/webhook/webhook.zip --profile g_h_scrabble
cd ../ocr
zip -r ocr.zip python
aws s3 cp ocr.zip s3://$POLLINATORARTIFACTBUCKET/lambda_layers/ocr/ocr.zip --profile g_h_scrabble
cd ../flaskapp
zip -r flaskapp.zip python
aws s3 cp flaskapp.zip s3://$POLLINATORARTIFACTBUCKET/lambda_layers/flaskapp/flaskapp.zip --profile g_h_scrabble
cd ../html_to_image
zip -r html-to-image.zip python
aws s3 cp html-to-image.zip s3://$POLLINATORARTIFACTBUCKET/lambda_layers/html-to-image/html-to-image.zip --profile g_h_scrabble
```

<!-- Setting up a single layer for index.js to use.  This layer is from https://github.com/alixaxel/chrome-aws-lambda where the readme gives this set of instructions:

```
cd ..
zip -r9 ../imgkit_layer.zip .
cd ..
aws s3 cp puppeteer-layer.zip s3://$POLLINATORARTIFACTBUCKET/lambda_layers/html-to-image/puppeteer-layer.zip --profile g_h_scrabble
``` -->

```
aws s3 cp imgkit_layer.zip s3://$POLLINATORARTIFACTBUCKET/layer/imgkit_layer.zip --profile g_h_scrabble
```

Resources:
  MyLambdaFunction1:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: MyLambdaFunction1
      Handler: views.lambda_handler
      Runtime: python3.9
      Role: arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_EXECUTION_ROLE
      Code:
        S3Bucket: YOUR_S3_BUCKET_NAME
        S3Key: path/to/your/lambda_function_code.zip
      Layers:
        - Ref: MyLayer1
      Timeout: 30
      MemorySize: 128



# create a pipfile in the project directory

If it's not already installed, you will need to install wkhtmltopdf so that imgkit can use it.  If you haven't done sam build yet, this may not work since the .aws-sam directory structure is unbuilt.  You'll just have to come back and do this after doing one round of sam build

```
cd lambda_functions/webhook && \
zip -r webhook_package.zip webhook.py  && \
aws s3 cp webhook_package.zip s3://$POLLINATORARTIFACTBUCKET/lambda_functions/webhook/webhook_package.zip && \
rm webhook_package.zip

cd ../ocr  && \
zip -r ocr_package.zip ocr.py  && \
aws s3 cp ocr_package.zip s3://$POLLINATORARTIFACTBUCKET/lambda_functions/ocr/ocr_package.zip && \
rm ocr_package.zip

cd ../flaskapp && \
zip -r flaskapp_package.zip flaskapp.py static templates && \
aws s3 cp flaskapp_package.zip s3://$POLLINATORARTIFACTBUCKET/lambda_functions/flaskapp/flaskapp_package.zip && \
rm flaskapp_package.zip 

cd ../html-to-image && \
zip -r html-to-image.zip html_to_image_api.py && \
aws s3 cp html-to-image.zip s3://$POLLINATORARTIFACTBUCKET/lambda_functions/html-to-image/html-to-image.zip && \
rm html-to-image.zip 

cd ../..
```


<!-- Node js lambda function:

```
cd lambda_functions/html-to-image
zip -r html-to-image.zip .
aws s3 cp html-to-image.zip s3://$POLLINATORARTIFACTBUCKET/lambda_functions/html-to-image/html-to-image.zip --profile g_h_scrabble
cd ../..
``` -->

```
cd lambda_functions/ocr
pipenv --python 3.10
pipenv install pillow boto3
pipenv run pip freeze > requirements.txt
```

### AWS Cloudformation 

```
aws cloudformation deploy \
    --template-file packaged.yaml \
    --stack-name PollinatorServerlessStack \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides S3ArtifactBucketName=$POLLINATORARTIFACTBUCKET \
        S3OutputBucketName=$POLLINATOROUTPUTBUCKET \
        TwilioAccountSid=$TWILIOACCTSID \
        TwilioAuthToken=$TWILIOAUTHTOKEN \
        TwilioPhoneNumber=$TWILIOPHONENUMBER \
        RapidApiEndpoint=$RAPIDAPI_ENDPOINT \
        RapidApiHost=$RAPIDAPI_HOST \
        RapidApiKey=$RAPIDAPI_KEY \
    --profile g_h_scrabble
```

### update the Twilio Webhook Url:

```
cd twilio
pipenv shell
python twilio/update_twilio_webhook.py
```

### To delete errant stack:
```
aws cloudformation delete-stack --stack-name PollinatorServerless --profile g_h_scrabble
```

# Code Graveyard
### Sam build

```
sam build \
--region us-west-2 \
--template-file pollinator_serverless_cft.yaml \
--profile g_h_scrabble
```

### Deploy the packaged template using SAM CLI
```
<!-- cp /usr/local/bin/wkhtmltoimage .aws-sam/build/WebhookLambdaFunction/ -->
sam deploy \
    --template-file ./.aws-sam/build/template.yaml \
    --stack-name PollinatorServerless \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        S3BucketName=$POLLINATORBUCKET \
        TwilioAccountSid=$TWILIOACCTSID \
        TwilioAuthToken=$TWILIOAUTHTOKEN \
        TwilioPhoneNumber=$TWILIOPHONENUMBER \
        S3ArtifactBucketName=$POLLINATORARTIFACTBUCKET \
        S3OutputBucketName=$POLLINATOROUTPUTBUCKET \
    --s3-bucket $POLLINATORARTIFACTBUCKET \
    --profile g_h_scrabble
```

