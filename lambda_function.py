import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, date
import uuid

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
table = dynamodb.Table('Users')

# To check the validity of email address
def valid_email(email):
    return "@" in email and "." in email

# To check the validity of phone number
def valid_phone(phone):
    return phone.isdigit() and len(phone) == 10

# Converting the dob from 'string' format to the 'date' format for displaying to the user
def convert_string_to_date(date_str):
    try:
        parsed_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
        return parsed_date.date()
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

# Converting the dob from 'date' format to the 'string' format for storage into DynamoDB table 
def convert_date_to_string(date_obj):
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%Y-%m-%d")
    elif isinstance(date_obj, date):
        return date_obj.strftime("%Y-%m-%d")
    return None

# Lambda function to handle all the operations
def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters', {})
        user_id = path_parameters.get('user_id') if path_parameters else None

        if http_method == 'GET' and user_id:
            return get_user(user_id)
        elif http_method == 'GET':
            return get_users()
        elif http_method == 'POST':
            return create_user(event)
        elif http_method == 'PUT' and user_id:
            return update_user(user_id, event)
        elif http_method == 'DELETE' and user_id:
            return delete_user(user_id)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Invalid request method or parameters'})
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Internal server error: {str(e)}'})
        }

# Get all the users from the DynamoDB table 
def get_users():
    try:
        response = table.scan()  # Scan entire table
        for user in response.get('Items', []):
            if 'dob' in user and user['dob']:
                user['dob'] = convert_string_to_date(user['dob'])
                user['dob'] = convert_date_to_string(user['dob'])
        return {
            'statusCode': 200,
            'body': json.dumps(response['Items'])  
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"Error": e.response['Error']['Message']})
        }

# Get a specific user by ID
def get_user(user_id):
    try:
        response = table.get_item(
            Key={'id': str(user_id)}  # primary key 'id' of the User
        )
        user = response.get('Item')
        if user:
            if 'dob' in user and user['dob']:
                user['dob'] = convert_string_to_date(user['dob'])
                user['dob'] = convert_date_to_string(user['dob'])
            return {
                'statusCode': 200,
                'body': json.dumps(user)
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({"Error": "User not Found"}) 
            }
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"Error": e.response['Error']['Message']})
        }

# To shorten the User_Id
def generate_short_id(length=3):
    user_id = str(uuid.uuid4())  # Generate a regular user id
    return user_id.replace('-', '')[:length]  # Remove '-' and truncate to the specified length

# Add new user to the Database
def create_user(event):
    # Check if the request body is present with the Create event
    try:
        if not event.get('body'):
            return {
                'statusCode': 400,
                'body': json.dumps({"Error": "Request body is missing"})
            }
        # Check the format of request body (must be JSON format)
        try:
            data = json.loads(event['body'])    
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'body': json.dumps({"Error": "Invalid JSON format"})
            }

        required_fields = ["lastname", "dob", "address", "gender", "email", "phone_no"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        # Display the error and missing fields(if any)
        if missing_fields:
            return {
                'statusCode': 400,
                'body': json.dumps({"Error": "Missing required fields", "Missing Fields": missing_fields})
            }
        # Check validity of the email id 
        if not valid_email(data['email']):
            return {
                'statusCode': 400,
                'body': json.dumps({"Error": "Invalid Email"})
            }
        # Check validity of the phone no.
        if not valid_phone(data['phone_no']):
            return {
                'statusCode': 400,
                'body': json.dumps({"Error": "Invalid Phone Number"})
            }

        try:
            dob_str = data["dob"]
            dob = convert_string_to_date(dob_str)     # Convert the string input of dob into 'date' format
        except ValueError:
            return {
                'statusCode': 400,
                'body': json.dumps({"Error": "Invalid Date Format, Please use YYYY-MM-DD format"})
            }

        # Generating a short User_id  
        user_id = generate_short_id(length=3)

        user = {
            "id": user_id,
            "lastname": data["lastname"],
            "dob": convert_date_to_string(dob),     # converting dob to string format for insertion into DynamoDB table
            "address": data["address"],
            "gender": data["gender"],
            "email": data["email"],
            "phone_no": data["phone_no"]
        }

        try:
            table.put_item(Item=user)             # Insert the new data into the 'Users' table in DynamoDB
        except ClientError as e:
            return {
                'statusCode': 500,
                'body': json.dumps({"Error": e.response['Error']['Message']})     # When not connected to DynamoDB
            }

        return {
            'statusCode': 201,                      # Successfully Created New User 
            'body': json.dumps(user)    
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"Error": f"Internal error: {str(e)}"})   # Internal Server Error
        }

# Update user information by using the User_id
def update_user(user_id, event):

    try:
        response = table.get_item(Key={'id': str(user_id)})
        user = response.get('Item')
        # When User_id is not present in the 'Users' table
        if not user:
            return {
                'statusCode': 404,
                'body': json.dumps({"Error": "User not found"})
            }
        # Check the presence of 'request body' with the Update event 
        if not event.get('body'):
            return {
                'statusCode': 400,
                'body': json.dumps({"Error": "Request body is missing"})
            }
        # Check the format of the request body (must be JSON)
        try:
            data = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'body': json.dumps({"Error": "Invalid JSON format"})
            }
        # Updating set of expressions for particular User_id
        update_expression = "SET "
        expression_values = {}
        update_fields = False

        # Updating the lastname
        if "lastname" in data:
            update_expression += "lastname = :lastname, "
            expression_values[":lastname"] = data["lastname"]
            update_fields = True
        # Updating the dob
        if "dob" in data:
            dob = convert_string_to_date(data["dob"])
            if not dob:
                return {
                    'statusCode': 400,
                    'body': json.dumps({"Error": "Invalid date format, please use YYYY-MM-DD"})
                }
            update_expression += "dob = :dob, "
            expression_values[":dob"] = convert_date_to_string(dob)
            update_fields = True
        # Updating the address
        if "address" in data:
            update_expression += "address = :address, "
            expression_values[":address"] = data["address"]
            update_fields = True
        # Updating the gender
        if "gender" in data:
            update_expression += "gender = :gender, "
            expression_values[":gender"] = data["gender"]
            update_fields = True
        # Updating the email 
        if "email" in data:
            if not valid_email(data["email"]):
                return {
                    'statusCode': 400,
                    'body': json.dumps({"Error": "Invalid email format"})
                }
            update_expression += "email = :email, "
            expression_values[":email"] = data["email"]
            update_fields = True
        # Updating the phone_no
        if "phone_no" in data:
            if not valid_phone(data["phone_no"]):
                return {
                    'statusCode': 400,
                    'body': json.dumps({"Error": "Invalid phone number format"})
                }
            update_expression += "phone_no = :phone_no, "
            expression_values[":phone_no"] = data["phone_no"]
            update_fields = True

        # Remove the last comma from the update expression 
        if update_fields:
            update_expression = update_expression.rstrip(', ')

            try:
                # Update operation in DynamoDB
                table.update_item(
                    Key={'id': user_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values
                )
                # Fetch updated user data
                updated_user = table.get_item(Key={'id': user_id}).get('Item')

                # Return the updated user information
                return {
                    'statusCode': 200,
                    'body': json.dumps(updated_user)
                }
            except ClientError as e:
                return {
                    'statusCode': 500,
                    'body': json.dumps({"Error": e.response['Error']['Message']})
                }
        # Error when no fields are provided for Update event
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({"Error": "No valid fields to update"})
            }
    # Internal Server Error
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"Error": f"Internal error: {str(e)}"})
        }

# Delete a user by User_id
def delete_user(user_id):
    try:
        response = table.get_item(Key={'id': user_id})
        user = response.get('Item')
        if not user:
            return {
                'statusCode': 404,
                'body': json.dumps({"Error": "User not found"})
            }

        # Delete operation
        table.delete_item(Key={'id': user_id})

        return {
            'statusCode': 200,
            'body': json.dumps({"Message": "User successfully deleted"})
        }
    # Internal Server Error
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"Error": e.response['Error']['Message']})
        }
