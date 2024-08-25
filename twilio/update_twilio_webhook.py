import os
import boto3
from twilio.rest import Client

# Retrieve environment variables
twilio_phone_number = os.getenv('TWILIOPHONENUMBER')
twilio_phone_number_sid = os.getenv('TWILIOPHONENUMBERSID')
twilio_account_sid = os.getenv('TWILIOACCTSID')
twilio_auth_token = os.getenv('TWILIOAUTHTOKEN')

# AWS profile and stack details
aws_profile = 'g_h_scrabble'
stack_name = 'PollinatorServerless'
output_key = 'ApiGatewayUrlSms'

# Initialize boto3 session with the specified profile
session = boto3.Session(profile_name=aws_profile)
cf_client = session.client('cloudformation')

# Retrieve the API Gateway URL from the CloudFormation stack output
response = cf_client.describe_stacks(StackName=stack_name)
outputs = response['Stacks'][0]['Outputs']
api_gateway_url = next(output['OutputValue'] for output in outputs if output['OutputKey'] == output_key)

# Initialize Twilio client
twilio_client = Client(twilio_account_sid, twilio_auth_token)

# Update the Twilio webhook
twilio_client.incoming_phone_numbers(twilio_phone_number_sid).update(
    sms_url=api_gateway_url
)

print(f"Twilio webhook updated to: {api_gateway_url}")