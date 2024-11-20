# User-Management-API
* ## User Management API using AWS and NoSQL

This project provides a Serverless REST API that manages user data with the help of AWS DynamoDB and AWS Lambda with API Gateway. 
This User Management API focuses on performing CRUD(Create-Read-Update-Delete) operations along with handling the possible errors and validation checks. 

The API supports the following operations: 
##### 1. GET /users: Endpoint that returns all the users present in DynamoDB table
##### 2. GET /users/{user_id}: Endpoint that is used to retrieve a specific user by using their User_Id
##### 3. POST /users: Endpoint that is used to create a new user entry in the DynamoDB table
##### 4. DELETE /users/{user_id}: Endpoint that is used to Delete a user by using User_Id
##### 5. PUT /users/{user_id}: Endpoint that is used to Update user details for specific user by using their User_Id

* ## Key Features

##### 1. AWS DynamoDB Integration
The API uses DynamoDB to store and manage the user data. The table is designed to store the User information using the following schema: 
* ###### id : Unique user identifier
* ###### lastname: Lastname of the user
* ###### dob: Date of Birth (YYYY-MM-DD format)
* ###### address: Address of the user
* ###### gender: Gender of the user
* ###### email: Email id of the user
* ###### phone_no: Contact number of the user

##### 2. AWS Lambda Function
The Lambda function is used to write the main business logic that is used for handling the user data in the AWS DynamoDB. It allows the application to run without provisioning or managing the servers. Each of the above operations are mapped to specific HTTP methods (GET, POST, PUT, DELETE) and is handled by the Lambda function.

##### 3. Entry Validation 
Validation of the entries provided are done for email, phone and dob. 
* ###### email: For POST and PUT requests the email of user is validated to ensure basic email format
* ###### phone_no: It should be 10 digits and numeric characters only
* ###### dob: Date of Birth must follow YYYY-MM-DD format

##### 4. Short User ID
For the user record, the API generates a short User_Id (3 characters) by taking the first 3 characters of the UUID generated for every new user entry. It ensure that every user have a short, simple and unique User_Id. 

##### 5. Data Handling
For storing the dob in the DynamoDB table, it is converted into 'string' format. Further, while retrieving the dob from the DynamoDB table it is converted back to 'date' format. 



