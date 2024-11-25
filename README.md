# PollinatorServerless

## TODOs
- rebuild
- include an architecture diagram
- tear down everything and pull to a new directory from origin and follow the README for installation to make sure it's all there in order
- push back to origin!

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

We need environmental variables for two S3 buckets:
$POLLINATORARTIFACTBUCKET: this is where the Lambda layers will go
$POLLINATOROUTPUTBUCKET: this is where temporary files such as output PDF will go.  It has public access so that Twilio can grab the PDF

```
export POLLINATOROUTPUTBUCKET=pollinatorserverless
export POLLINATORARTIFACTBUCKET=pollinatorserverlessartifact
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

# zip and upload lambdas and dependencies to S3 in *_package.zip

```
cd lambda_functions/webhook && \
rm -rf package
mkdir -p package
python3.9 -m pip install -t ./package requests twilio boto3 
cd package
zip -r ../webhook_package.zip .
cd ..
zip webhook_package.zip webhook.py
aws s3 cp webhook_package.zip s3://$POLLINATORARTIFACTBUCKET/lambda_functions/webhook/webhook_package.zip && \
rm webhook_package.zip

cd ../ocr  && \
rm -rf package
mkdir -p package
python3.9 -m pip install -t ./package boto3 
cd package
zip -r ../ocr_package.zip .
cd ..
zip ocr_package.zip ocr.py
aws s3 cp ocr_package.zip s3://$POLLINATORARTIFACTBUCKET/lambda_functions/ocr/ocr_package.zip && \
rm ocr_package.zip

cd ../flaskapp && \
rm -rf package
mkdir -p package
python3.9 -m pip install -t ./package flask==2.0.3 werkzeug==2.0.3 flask_lambda requests beautifulsoup4 pytz 
cd package
zip -r ../flaskapp_package.zip .
cd ..
zip flaskapp_package.zip flaskapp.py templates/*
aws s3 cp flaskapp_package.zip s3://$POLLINATORARTIFACTBUCKET/lambda_functions/flaskapp/flaskapp_package.zip && \
rm flaskapp_package.zip 
cd ../..
```


## IAM

Prior to any cloudformation stack creation, you should always check that the CFT lints:

```
cfn-lint pollinator_serverless_cft.yaml
```

### AWS Cloudformation 

```
aws cloudformation deploy \
    --template-file pollinator_serverless_cft.yaml \
    --stack-name PollinatorServerlessStack \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides S3ArtifactBucketName=$POLLINATORARTIFACTBUCKET \
        S3OutputBucketName=$POLLINATOROUTPUTBUCKET \
        TwilioAccountSid=$TWILIOACCTSID \
        TwilioAuthToken=$TWILIOAUTHTOKEN \
        TwilioPhoneNumber=$TWILIOPHONENUMBER \
    --profile g_h_scrabble
```

### update the Twilio Webhook Url:

Do this to update the url for the webhook in Twilio:

```
cd twilio
pipenv shell
python update_twilio_webhook.py
```

### To delete errant stack:
```
aws cloudformation delete-stack --stack-name PollinatorServerless --profile g_h_scrabble
```

### Example creating a requirements.txt
```
cd lambda_functions/ocr
pipenv --python 3.10
pipenv install pillow boto3
pipenv run pip freeze > requirements.txt
```
