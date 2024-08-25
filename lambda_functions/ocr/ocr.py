import boto3
import json
import base64

def lambda_handler(event, context):
    print(event)
    
    # Parse the JSON body
    body = json.loads(event['body'])
    
    if 'image_bytes' not in body:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'image_bytes key not found in body'})
        }
    
    image_bytes = body['image_bytes'].encode('ISO-8859-1')
    
    # Perform OCR using AWS Rekognition
    rekognition = boto3.client('rekognition')
    response = rekognition.detect_text(
        Image={
            'Bytes': image_bytes
        }
    )
    
    # Process the OCR response
    text_detections = response['TextDetections']
    detected_text = ' '.join([detection['DetectedText'] for detection in text_detections])
    print(detected_text)
    return {
        'statusCode': 200,
        'body': json.dumps({'detected_text': detected_text})
    }