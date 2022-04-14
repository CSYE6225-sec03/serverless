import json
import boto3
import uuid
import time
import os
from boto3.dynamodb.conditions import Key, Attr

def sendEmail(event, context):

    message = event['Records'][0]['Sns']['Message']

    print(message)

    reset_req = json.loads(message)

    emailAddress = reset_req["emailAddress"]
    messageType = reset_req["messageType"]
    token = reset_req["token"]
    id = insert_to_dynamodb(emailAddress, token)
    if id:
        prepare_and_send_email(emailAddress, id)
    else:
        print("No Auth")




def insert_to_dynamodb(recipient, token):
    dynamo_table = "verification"
    dynamodb = boto3.resource('dynamodb',region_name='us-east-1')
    table = dynamodb.Table(dynamo_table)
    id = token
    dynamo_row = table.query(
        KeyConditionExpression=Key('email').eq(recipient)
    )
    items = dynamo_row['Items']

    if not items:
        response = table.put_item(
        Item={
            'UniqueToken': id,
            'email': recipient,
            'CreationTime' : str(time.time()),
            'ExpirationTime' : str(time.time() + 300)
            }
        )
        print("New record inserted successfully")
        return id
    elif items:
        dt = float(items[0]['CreationTime'])
        currentTime = float(time.time())
        time_diff_minutes = (currentTime - dt)/60
        if time_diff_minutes<=5.0:
            print("Requested token within TTL")
        else:
            # uid = uuid.uuid4()
            id = token
            table.update_item(
            Key={
                'Email' : recipient
            },
            UpdateExpression="set UniqueToken = :t, CreationTime = :c, ExpirationTime = :e",
            ExpressionAttributeValues={
            ':t': id,
            ':c': str(time.time()),
            ':e': str(time.time() + 300)
        },
            ReturnValues="UPDATED_NEW"
        )
            return id

def prepare_and_send_email(recipient, token):
    # Sender Email ID. Dummy email which will be used to send emails.
    SENDER = "hu.chun@northeastern.edu"


    password_reset_link = "http://prod.chunjunhu.me" + "/v1/verifyUserEmail?email=" + recipient +"&token=" + token

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = (
                    password_reset_link + "\r\n"
                )

    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
      <h1>Verify Link for Email Address</h1>
      <p>
        <br><br>
        """ + password_reset_link + """
        <br><br>
        This link will be active for 5 minutes only.
      </p>
    </body>
    </html>
                """

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # The subject line for the email.
    SUBJECT = "Verify Email Address"

    #Sending the mail
    trigger_email(recipient, BODY_HTML, BODY_TEXT, SUBJECT, CHARSET, SENDER)



def trigger_email(recipient, BODY_HTML, BODY_TEXT, SUBJECT, CHARSET, SENDER):


    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name='us-east-1')
    # Try to send the email.

    #Provide the contents of the email.
    response = client.send_email(
        Destination={
            'ToAddresses': [
                recipient,
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': CHARSET,
                    'Data': BODY_HTML,
                },
                'Text': {
                    'Charset': CHARSET,
                    'Data': BODY_TEXT,
                },
            },
            'Subject': {
                'Charset': CHARSET,
                'Data': SUBJECT,
            },
        },
        Source=SENDER,
    )







