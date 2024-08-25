# PollinatorServerless

## Twilio:

```
refs to how to get secrets placeholder
```

simple send to Twilio: 
```
curl 'https://api.twilio.com/2010-04-01/Accounts/[REDACTED]/Messages.json' -X POST \
--data-urlencode 'To=+[REDACTED]' \
--data-urlencode 'Body=Hello from Twilio' \
--data-urlencode 'From=[REDACTED]' \
-u [REDACTED]:[AuthToken]
```

(sends a message to Gary's phone WORKS!)

### Set the environment variable for the S3 bucket name

```
export POLLINATORBUCKET=pollinatorserverless
```

## IAM

```
cfn-lint pollinator_serverless_cft.yaml
```


### Create Bucket first as sam deploy will need it to upload code to.
```
aws s3api create-bucket --bucket $POLLINATORBUCKET \
--region us-west-2 \
--create-bucket-configuration LocationConstraint=us-west-2 \
--profile g_h_scrabble
```

# create a pipfile in the project directory
```
cd lambda_functions
pipenv --python 3.8
pipenv install boto3 requests twilio
pipenv run pip freeze > requirements.txt
```

# Create and activate a virtual environment
```
pipenv install
pipenv shell
pipenv install -r requirements.txt
pipenv lock --requirements > requirements.txt
cp requirements.txt lambda_functions/ocr
cp requirements.txt lambda_functions/webhook 
```

### Sam build
```
sam build \
--region us-west-2 \
--template-file pollinator_serverless_cft.yaml \
--profile g_h_scrabble
```

### Deploy the packaged template using SAM CLI
```
sam deploy \
    --template-file ./.aws-sam/build/template.yaml \
    --stack-name PollinatorServerless \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        S3BucketName=$POLLINATORBUCKET \
        TwilioAccountSid=$TWILIOACCTSID \
        TwilioAuthToken=$TWILIOAUTHTOKEN \
    --s3-bucket $POLLINATORBUCKET \
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

## Return OCR to user:

Yes, it is possible to set up a workflow where your Twilio number receives a text message with an image, processes the image using OCR (Optical Character Recognition) with AWS services, and then returns the extracted text to the original sender. Here is a high-level overview of the steps involved:

Receive SMS with Twilio:

Configure your Twilio number to receive SMS messages.
Set up a webhook in Twilio that triggers an AWS Lambda function when an SMS is received.
Forward the Image to AWS:

The Lambda function receives the image URL from the SMS.
The Lambda function downloads the image from the URL.
Process the Image with OCR:

Use AWS Textract or another OCR service to extract text from the image.
Send the Extracted Text Back:

Use Twilio's API to send the extracted text back to the original sender.
Pseudocode for the Workflow
Twilio Webhook:

Configure Twilio to call an AWS API Gateway endpoint when an SMS is received.
AWS Lambda Function:

The Lambda function is triggered by the API Gateway.
The function downloads the image from the URL provided in the SMS.
The function processes the image using AWS Textract.
The function sends the extracted text back to the original sender using Twilio's API.
Example AWS Lambda Function Pseudocode
Summary
Twilio: Set up a webhook to trigger an AWS Lambda function when an SMS is received.
AWS Lambda: Download the image, process it with OCR, and send the extracted text back to the sender.
AWS Textract: Use for OCR processing.
Twilio API: Use to send the extracted text back to the sender.
This workflow can be implemented using AWS SAM or CloudFormation for deployment and configuration.

Yes, you can extend the workflow to handle a series of images. The process would involve modifying the Lambda function to handle multiple image URLs and process each one sequentially or concurrently. Here’s a high-level overview of the steps involved:

Receive SMS with Multiple Image URLs:

Configure your Twilio number to receive SMS messages containing multiple image URLs.
Set up a webhook in Twilio that triggers an AWS Lambda function when an SMS is received.
Forward the Images to AWS:

The Lambda function receives the image URLs from the SMS.
The Lambda function downloads each image from the URLs.
Process the Images with OCR:

Use AWS Textract or another OCR service to extract text from each image.
Send the Extracted Texts Back:

Use Twilio's API to send the extracted texts back to the original sender.
Pseudocode for the Workflow
Twilio Webhook:

Configure Twilio to call an AWS API Gateway endpoint when an SMS is received.
AWS Lambda Function:

The Lambda function is triggered by the API Gateway.
The function downloads each image from the URLs provided in the SMS.
The function processes each image using AWS Textract.
The function sends the extracted texts back to the original sender using Twilio's API.
Example AWS Lambda Function Pseudocode
Summary
Twilio: Set up a webhook to trigger an AWS Lambda function when an SMS with multiple image URLs is received.
AWS Lambda: Download each image, process them with OCR, and send the combined extracted text back to the sender.
AWS Textract: Use for OCR processing.
Twilio API: Use to send the combined extracted text back to the sender.
This workflow can be implemented using AWS SAM or CloudFormation for deployment and configuration.

## Python to get new api endpoint and write it to Twilio

You're correct. Twilio will not have access to AWS Parameter Store, so you will need to manually update the webhook URL in the Twilio console whenever the API Gateway endpoint changes. However, you can automate the process of retrieving the new API Gateway URL and updating the Twilio webhook using a script.

Automating the Update of Twilio Webhook URL
Retrieve the API Gateway URL: Use the AWS CLI to get the API Gateway URL after deploying the stack.

Update Twilio Webhook: Use the Twilio API to update the webhook URL programmatically.

Example Script to Automate the Process
Here's a Python script that retrieves the API Gateway URL and updates the Twilio webhook:



Caveat emptor, but ok... 

## Old Info from Github CoPilot

Yes, it's possible to integrate Twilio with AWS to send text images for processing with Amazon Textract. Here is a high-level overview of the steps involved:

Receive SMS with Twilio: Use Twilio to receive SMS messages that contain text images.
Forward the Image to AWS: Use Twilio's webhook to trigger an AWS Lambda function when an SMS is received.
Process the Image with Textract: In the Lambda function, use the AWS SDK to send the image to Amazon Textract for processing.
Step-by-Step Plan
Set up Twilio to receive SMS:

Create a Twilio account and get a phone number.
Set up a webhook in Twilio to forward incoming SMS to an AWS API Gateway endpoint.
Create an AWS API Gateway:

Create an API Gateway endpoint that triggers an AWS Lambda function.
Create an AWS Lambda Function:

Write a Lambda function that receives the image from Twilio, stores it in an S3 bucket, and then calls Amazon Textract to process the image.
Process the Image with Amazon Textract:

Use the AWS SDK to call Textract and extract text from the image.
Example Code
Twilio Webhook (Python Flask Example)

Additional Steps
Configure AWS IAM Roles: Ensure your Lambda function has the necessary permissions to access S3 and Textract.
Deploy the Flask App: Deploy the Flask app to a server or a service like AWS Elastic Beanstalk.
Test the Integration: Send an SMS with an image to your Twilio number and verify the end-to-end flow.
This is a simplified example to get you started. You may need to handle additional error checking, security, and scalability considerations for a production environment.

Steps to Deploy:
Create a virtual environment and install dependencies:

Download the Tesseract-OCR binary:

You can download the Tesseract binary from the official repository or use a precompiled binary suitable for AWS Lambda.
Package the Lambda function:

Upload the deployment package to AWS Lambda:

Go to the AWS Lambda console, create a new function, and upload the function.zip file.
Configure the Lambda function:

Set the handler to lambda_function.lambda_handler.
Set the necessary environment variables and permissions.
This setup will allow you to use pytesseract for OCR in your AWS Lambda function.


## Building the layer and zip file:

Here's how you can proceed:

Build the Layer Locally:

Create a directory for your layer, for example: ~/Documents/play/PollinatorServerless/PollinatorServerless/lambda/layer.
Inside this directory, create a python directory and install the necessary packages (pytesseract and Pillow) into it.
Zip the Layer:

Navigate to the layer directory and zip the contents.
Upload the Layer to S3:

Upload the layer.zip file to your S3 bucket.

## and More:

Steps to Deploy:
Create a virtual environment and install dependencies:

python3 -m venv venv
source venv/bin/activate
pip install pytesseract pillow

Download the Tesseract-OCR binary:

You can download the Tesseract binary from the official repository or use a precompiled binary suitable for AWS Lambda.
Package the Lambda function:

deactivate
cd venv/lib/python3.*/site-packages
zip -r9 ${OLDPWD}/function.zip .
cd ${OLDPWD}
zip -g function.zip lambda_function.py
zip -g function.zip /path/to/tesseract


Upload the deployment package to AWS Lambda:
