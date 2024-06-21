# Initialize the FastAPI application and database
# Initialize the SQS client
# Process messages from the SQS queue
# Send notifications
# Define API endpoints

# Initialize the SQS client
#sqs_client = boto3.client('sqs', region_name='us-east-2')

import crud, models, schemas, database
from database import engine, SessionLocal
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import boto3
import json
import threading
import time
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from contextlib import asynccontextmanager

# Create the database tables
models.Base.metadata.create_all(bind=engine)

# Initialize the SQS client
sqs_client = boto3.client('sqs', region_name='us-east-2')

# SQS queue URL
QUEUE_URL = 'https://sqs.us-east-2.amazonaws.com/767397896582/MyQueue.fifo'

# Function to process messages from the SQS queue
def process_messages():
    print("Starting to process messages from SQS")
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )

            messages = response.get('Messages', [])
            if not messages:
                print("No messages received")
            for message in messages:
                print(f"Raw message body: {message['Body']}")  # Add this line for debugging

                try:
                    body = json.loads(message['Body'])
                    print(f"Received message: {body}")

                    # Just print out whatever is in SQS, could send out emails/sms from here
                    send_notification(body)

                    sqs_client.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Failed message: {message['Body']}")
        except NoCredentialsError:
            print("Credentials not available")
        except PartialCredentialsError:
            print("Incomplete credentials provided")
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(5)

# Example function to send a notification (e.g., email, SMS)
def send_notification(message):
    # Implement your notification logic here
    print(f"Sending notification for booking ID: {message['booking_id']}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Lifespan startup")
    # Start processing messages from the SQS queue in a background thread
    thread = threading.Thread(target=process_messages, daemon=True)
    thread.start()
    yield
    print("Lifespan shutdown")
    # Any cleanup code can go here, but in this case, we don't have any

# Initialize the FastAPI application with lifespan
app = FastAPI(lifespan=lifespan)

# Endpoint to create a notification
@app.post("/notifications/", response_model=schemas.Notification)
def create_notification(notification: schemas.NotificationCreate, db: Session = Depends(database.get_db)):
    return crud.create_notification(db=db, notification=notification)

# Endpoint to read a notification by ID
@app.get("/notifications/{notification_id}", response_model=schemas.Notification)
def read_notification(notification_id: int, db: Session = Depends(database.get_db)):
    db_notification = crud.get_notification(db, notification_id=notification_id)
    if db_notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return db_notification








