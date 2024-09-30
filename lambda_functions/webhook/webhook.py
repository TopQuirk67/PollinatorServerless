import os
import requests
import logging
import urllib.parse
from twilio.rest import Client
import boto3
import uuid
# import imgkit
# from weasyprint import HTML
# from PIL import Image, ImageDraw, ImageFont
# from io import BytesIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client('s3')

def handle_images(image_urls):
    ocr_lambda_url = os.environ['OCR_API_ENDPOINT']
    twilio_account_sid = os.environ['TWILIO_ACCOUNT_SID']
    twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
    combined_results = []

    for image_url in image_urls:
        response = requests.get(image_url, auth=(twilio_account_sid, twilio_auth_token))
        if response.status_code == 200:
            image_bytes = response.content
            payload = {"image_bytes": image_bytes.decode('ISO-8859-1')}
            # logger.info("Payload to OCR Lambda: %s", payload)
            ocr_response = requests.post(ocr_lambda_url, json=payload)
            # print(ocr_response.text)
            if ocr_response.status_code == 200:
                combined_results.extend([word.strip() for word in ocr_response.text.split("\n")])
            else:
                logger.error("OCR Lambda function returned an error: %s", ocr_response.text)
        else:
            logger.error("Failed to fetch image from URL: %s", image_url)

    # Process combined_results to lowercase, trim, make unique, and sort
    processed_results = sorted(set(word.lower().strip() for word in combined_results))
    
    return processed_results

def create_html_table(text_list):
    html_content = "<html><body><table border='1'>"
    for word in text_list:
        html_content += f"<tr><td>{word}</td></tr>"
    html_content += "</table></body></html>"
    return html_content


def create_image_from_html(html_content, s3_bucket, s3_key):
    # Generate image from HTML using imgkit
    image_path = f"/tmp/{uuid.uuid4()}.png"
    imgkit.from_string(html_content, image_path)
    
    # Upload image to S3
    with open(image_path, 'rb') as image_file:
        s3_client.put_object(Bucket=s3_bucket, Key=s3_key, Body=image_file, ContentType='image/png')
    
    # Generate a pre-signed URL with a one-hour expiration
    s3_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': s3_bucket, 'Key': s3_key},
        ExpiresIn=3600  # 1 hour in seconds
    )
    
    return s3_url


# def create_image_from_html(html_content, s3_bucket, s3_key):
#     # Create an image from HTML content using Pillow
#     image = Image.new('RGB', (800, 600), color=(255, 255, 255))
#     draw = ImageDraw.Draw(image)
    
#     # Use a truetype font
#     font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
#     font = ImageFont.truetype(font_path, 15)
    
#     # Draw the HTML content as text (simplified example)
#     draw.text((10, 10), html_content, fill=(0, 0, 0), font=font)
    
#     # Save the image to a BytesIO object
#     image_bytes = BytesIO()
#     image.save(image_bytes, format='PNG')
#     image_bytes.seek(0)
    
#     # Upload image to S3
#     s3_client.put_object(Bucket=s3_bucket, Key=s3_key, Body=image_bytes, ContentType='image/png')
    
#     # Generate a pre-signed URL with a one-hour expiration
#     s3_url = s3_client.generate_presigned_url(
#         'get_object',
#         Params={'Bucket': s3_bucket, 'Key': s3_key},
#         ExpiresIn=3600  # 1 hour in seconds
#     )
    
#     return s3_url


# def create_pdf_from_html(html_content, s3_bucket, s3_key):
#     # Convert HTML to PDF
#     pdf = HTML(string=html_content).write_pdf()
    
#     # Upload PDF to S3
#     s3_client.put_object(Bucket=s3_bucket, Key=s3_key, Body=pdf, ContentType='application/pdf')
    
#     # Generate a pre-signed URL with a one-hour expiration
#     s3_url = s3_client.generate_presigned_url(
#         'get_object',
#         Params={'Bucket': s3_bucket, 'Key': s3_key},
#         ExpiresIn=3600  # 1 hour in seconds
#     )
    
#     return s3_url

# def create_image_from_html(html_content, output_path):
#     imgkit.from_string(html_content, output_path)

# def upload_image_to_s3(image_path, bucket_name, object_name):
#     s3_client = boto3.client('s3')
#     s3_client.upload_file(image_path, bucket_name, object_name)
    
#     # Set the expiration time for the object to 1 hour
#     s3_client.put_object_tagging(
#         Bucket=bucket_name,
#         Key=object_name,
#         Tagging={
#             'TagSet': [
#                 {
#                     'Key': 'expiration',
#                     'Value': '3600'  # 1 hour in seconds
#                 }
#             ]
#         }
#     )
    
#     return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"

def send_mms(to_phone_number, media_url):
    twilio_account_sid = os.environ['TWILIO_ACCOUNT_SID']
    twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_phone_number = os.environ['TWILIO_PHONE_NUMBER']
    
    client = Client(twilio_account_sid, twilio_auth_token)
    
    message = client.messages.create(
        body="Here is your Bee",
        from_=twilio_phone_number,
        to=to_phone_number,
        media_url=[media_url]
    )
    
    return message.sid

def create_image_from_html(html_content):
    try:
        # Prepare the payload for createimage Lambda
        s3_bucket = os.environ['OUTPUT_BUCKET']
        s3_key = f"images/{uuid.uuid4()}.jpg"
        createimage_lambda_function = os.environ['CREATEIMAGE_LAMBDA_FUNCTION']
        createimage_payload = json.dumps({
            'body': {
                'html_content': html_content
            }
        })

        # Invoke the createimage Lambda function

        response = lambda_client.invoke(
            FunctionName=createimage_lambda_function,  
            InvocationType='RequestResponse',
            Payload=createimage_payload
        )

        # Parse the response from createimage Lambda
        response_payload = json.loads(response['Payload'].read())
        if response['StatusCode'] != 200:
            raise Exception(f"Error invoking Lambda function: {response_payload}")

        # Extract the image URL from the response payload
        body = json.loads(response_payload['body'])
        if 'image_url' not in body:
            raise Exception("image_url not found in Lambda response")

        image_url = body['image_url']
        return image_url
        # jpg_base64 = json.loads(response_payload['body']).get('image', '')

        # # Decode the base64 string to get the PDF data
        # jpg_data = base64.b64decode(jpg_base64)

        # # Save the PDF to S3
        # s3_bucket = os.environ['OUTPUT_BUCKET']
        # s3_key = f"images/{uuid.uuid4()}.jpg"
        # s3_client = boto3.client('s3')
        # s3_client.put_object(Bucket=s3_bucket, Key=s3_key, Body=jpg_data)

        # # Generate the S3 URL
        # img_url = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"
        # print(img_url)
        # return img_url

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

### TODO: this is the next step to get this to the flaskapp Lambda.
# # Convert the list to JSON
# payload = json.dumps({"word_list": combined_results})

# # API Gateway endpoint URL
# api_gateway_url = "https://your-api-gateway-endpoint.amazonaws.com/your-stage/your-resource"

# # Send the payload to the API Gateway endpoint
# response = requests.post(api_gateway_url, data=payload, headers={"Content-Type": "application/json"})

# # Print the response from the Lambda function
# print(response.text)
    if from_phone_number:
        # Create an HTML table from the combined_results
        html_content = create_html_table(combined_results)
        logger.info("HTML:\n",html_content)
        
        if html_content is None:
            logger.error("Failed to generate HTML content")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to generate HTML content'})
            }


        logger.info("HTML:\n%s",html_content)

        # # Generate an image from the HTML content
        # image_url = create_image_from_html(html_content)

        # # Send the S3 URL to Twilio
        # results_message = s3_url
        # message_sid = send_mms(from_phone_number, results_message)
        # print(f"Message sent with SID: {message_sid}")

        # return {
        #     'statusCode': 200,
        #     'body': 'Results sent to your phone number'
        # }
        # Create image from HTML and get the S3 URL
        image_url = create_image_from_html(html_content)

        if not image_url:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to create image from HTML'})
            }

        # Send the S3 URL to Twilio
        message_sid = send_mms(from_phone_number, image_url)
        print(f"Message sent with SID: {message_sid}")
    
    return {
        'statusCode': 200,
        'body': 'Results sent to your phone number'
    }


