import os
import requests
import logging
import urllib.parse
from twilio.rest import Client
import boto3
import uuid
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client('s3')
OUTPUT_BUCKET = os.getenv('OUTPUT_BUCKET')
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_PHONE_NUMBER = os.environ['TWILIO_PHONE_NUMBER']
OCR_LAMBDA_FUNCTION_NAME = os.environ['OCR_LAMBDA_FUNCTION_NAME']
OUTPUT_MESSAGE = os.environ['OUTPUT_MESSAGE']

def handle_images(image_urls):
    lambda_client = boto3.client('lambda')
    twilio_account_sid = TWILIO_ACCOUNT_SID
    twilio_auth_token = TWILIO_AUTH_TOKEN
    combined_results = []

    for image_url in image_urls:
        response = requests.get(image_url, auth=(twilio_account_sid, twilio_auth_token))
        if response.status_code == 200:
            image_bytes = response.content
            payload = {"image_bytes": image_bytes.decode('ISO-8859-1')}
            # logger.info("Payload to OCR Lambda: %s", payload)
            try:
                ocr_response = lambda_client.invoke(
                    FunctionName=OCR_LAMBDA_FUNCTION_NAME,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                response_payload = json.loads(ocr_response['Payload'].read())
                if 'statusCode' in response_payload and response_payload['statusCode'] == 200:
                    combined_results.extend([word.strip() for word in response_payload['body'].split("\n")])
                else:
                    logger.error("OCR Lambda function returned an error: %s", response_payload)
            except Exception as e:
                logger.error(f"Failed to invoke OCR Lambda function: {e}")
        else:
            logger.error("Failed to fetch image from URL: %s", image_url)

    # Process combined_results to lowercase, trim, make unique, and sort
    processed_results = sorted(set(word.lower().strip() for word in combined_results))
    
    return processed_results

def upload_html_to_s3(html_content):
    s3_client = boto3.client('s3')
    short_uuid = str(uuid.uuid4())[:5]
    file_name = f"polli_{short_uuid}.html"
    try:
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=file_name,
            Body=html_content,
            ContentType='text/html',
        )
        url = f"https://{OUTPUT_BUCKET}.s3.amazonaws.com/{file_name}"
        logger.info(f"File uploaded successfully: {url}")
        return url
    except Exception as e:
        logger.error(f"Failed to upload file to S3: {e}")
        return None

def send_sms_via_twilio(to_phone_number, message_body):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        logger.info(f"Message sent: {message.sid}")
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")

    except Exception as e:
        print(f"Error in create_image_from_html: {e}")
        return None

def lambda_handler(event, context):
    # Extract image URLs from the event
    body = urllib.parse.parse_qs(event['body'])
    # logger.info("Parsed body: %s", body)
    num_media = int(body.get('NumMedia', [0])[0])
    image_urls = []
    from_phone_number = body.get('From', [None])[0]

    # Loop through the media URLs based on NumMedia
    for i in range(num_media):
        media_url_key = f'MediaUrl{i}'
        media_url = body.get(media_url_key)
        if media_url:
            image_urls.append(media_url[0])

    if not image_urls:
        return {
            'statusCode': 400,
            'body': 'No image URLs provided'
        }

    combined_results = handle_images(image_urls)

    if from_phone_number:
        # Create an HTML table from the combined_results
        lambda_client = boto3.client('lambda')
        # Prepare the payload for FlaskappLambdaFunction
        payload = {
            'body': json.dumps({'word_list': combined_results})
        }

        # Invoke the FlaskappLambdaFunction
        response = lambda_client.invoke(
            FunctionName=os.environ['FLASKAPP_LAMBDA_FUNCTION_NAME'],
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Parse the response
        response_payload = json.loads(response['Payload'].read())
        html_content = response_payload.get('body')        

        # logger.info(f"HTML:\n{html_content}")
        
        if html_content is None:
            logger.error("Failed to generate HTML content")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to generate HTML content'})
            }

        # Upload HTML to S3
        s3_url = upload_html_to_s3(html_content)
        if s3_url:
            # Send URL via Twilio
            logger.info(f"HTML content uploaded to S3: {s3_url}")
            message_body = f"{OUTPUT_MESSAGE} {s3_url}"
            send_sms_via_twilio(from_phone_number, message_body)
        else:
            logger.error("Failed to upload HTML to S3 and send SMS")
    
    return {
        'statusCode': 200,
        'body': 'Results sent to your phone number'
    }

if __name__ == "__main__":
    lambda_handler(None, None)