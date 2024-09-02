import boto3
import base64
import json
import logging
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Received event: %s", event)
    
    try:
        # Parse the body from the event
        body = json.loads(event['body'])
        # logger.info("Parsed body: %s", body)

        # Extract and log the base64 image data
        image_bytes = body['image_bytes']
        logger.info("Image bytes: %s", image_bytes)

        # Decode the base64 image data
        try:
            # Decode the image bytes from ISO-8859-1
            image_data = image_bytes.encode('ISO-8859-1')
            logger.info("Decoded image data length: %d", len(image_data))
            # image_data = base64.b64decode(image_bytes)
            # logger.info("Decoded image data length: %d", len(image_data))
        except base64.binascii.Error as e:
            logger.error("Base64 decoding error: %s", e)
            return {
                'statusCode': 400,
                'body': f"Base64 decoding error: {e}"
            }

        # Initialize Rekognition client
        rekognition = boto3.client('rekognition')

        # Call Rekognition to detect text in the image
        response = rekognition.detect_text(
            Image={'Bytes': image_data}
        )

        # Extract detected text
        detected_text = ' '.join([text['DetectedText'] for text in response['TextDetections'] if text['Type'] == 'LINE'])
        logger.info("Detected text: %s", detected_text)

        # Define the regular expression pattern
        pattern = r'\d{1,2}:\d{2}.*?Stats.*?(Beginner|Good Start|Moving Up|Good|Solid|Nice|Great|Amazing|Genius|Queen Bee) \d+ You have found \d+ words'
        # "8:19 Stats Yesterday More Genius 106 You have found 26 words Loyally Yahoo"
        # Search for the pattern in the detected text
        match = re.search(pattern, detected_text)
        
        if match:
            # Extract the segment after the matched pattern
            segment = detected_text[match.end():]
            
            # Process the segment to extract words
            words = segment.split()
            
            # Combine all words, remove duplicates, and sort alphabetically
            combined_words = sorted(set(words))
            
            logger.info("Combined words: %s", combined_words)  # Log the unique words for debugging

            return {
                'statusCode': 200,
                'body': '\n'.join(combined_words)
            }
        else:
            logger.error("Pattern not found in detected text")
            return {
                'statusCode': 400,
                'body': 'Pattern not found in detected text'
            }

    except KeyError as e:
        logger.error("KeyError: %s", e)
        return {
            'statusCode': 400,
            'body': f"KeyError: {e}"
        }

    except boto3.exceptions.Boto3Error as e:
        logger.error("Boto3Error: %s", e)
        return {
            'statusCode': 500,
            'body': f"Boto3Error: {e}"
        }

    except Exception as e:
        logger.error("Exception: %s", e)
        return {
            'statusCode': 500,
            'body': f"Exception: {e}"
        }