import json
import urllib.parse
import requests
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Parse the form-encoded body
    body = urllib.parse.parse_qs(event['body'])
    logger.info("Parsed body: %s", body)
    
    media_url = body.get('MediaUrl0', [None])[0]
    
    if media_url:
        logger.info("Media URL found: %s", media_url)
        # Download the image from the media URL with basic authentication
        twilio_account_sid = os.environ['TWILIO_ACCOUNT_SID']
        twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
        response = requests.get(media_url, auth=(twilio_account_sid, twilio_auth_token))
        if response.status_code == 200:
            image_bytes = response.content
            # Forward the image bytes to the OCR Lambda function via the API endpoint
            ocr_lambda_url = os.environ['OCR_API_ENDPOINT']
            payload = {"image_bytes": image_bytes.decode('ISO-8859-1')}
            logger.info("Payload to OCR Lambda: %s", payload)
            ocr_response = requests.post(ocr_lambda_url, json=payload)
            logger.info("OCR Lambda response: %s", ocr_response.text)
            return {
                'statusCode': 200,
                'body': ocr_response.text
            }
        else:
            logger.error("Failed to download image from URL: %s", media_url)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to download image'})
            }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'No MediaUrl0 found in the request'})
        }