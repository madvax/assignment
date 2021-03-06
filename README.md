# Assignment
This project holds the test automation test cases and defects for the Assignment.

H. Wilson, September 2020 

## The Approach 
Testing is mostly automated.
Test automation scripts are located in the test_cases folder.
A Regression Suits is located in the regression_test folder. 
The test cases in teh test_case folder are intended to be used to test individual features. 
The Regression Suite is intended to be ran to determine if a change to a features has had any 
unintended consequences. Test automation scripts can be executed individually or by a framework 
given the contract below:
- Passing tests return a 0 and failing tests return 100. Any other return codes indicate a test script error.

## Assumptions 
1. The Target of Evaluation (TOE) is the Darwin Version of the Server
2. The service should handle up to 100 simultaneous clients.
3. Passwords to be hashed should be of length 1 to 100 characters inclusive.
4. Passwords to be hashed should be of composed of letters, number and special characters.
5. The hashing server offers a five-second delay. 
6. An additional one-second delay is added for network latency.
7. Valid server port numbers are in the range 1025-65534 inclusive. 
8. The 'job identifier' returned may or may not be an integer. 
9. Successful calls to the API yield a status code of 200.
10. Unsuccessful calls to the API yield a status code of 404 (or 4xx)
    
## Defects Found 
unless otherwise specified all defects apply to darwin server version 0c3d817
1. Average response time returned by Get Status route is incorrect returns `{"TotalRequests":10,"AverageTime":86786}` when using call `curl http://127.0.0.1:8098/stats`. Expected response `{"TotalRequests":10,"AverageTime":5002}`
2. Get Status accepts additional data via query parameter '?data=value'. 
3. Cannot shutdown server via post hash route until it has processed at least one password hash request. ... sometimes.
4. Post Hash Shutdown command cosmetic issue - server does return a clean 200 but, the local server message is 
`2020/09/05 13:32:08 Shutdown signal recieved
2020/09/05 13:32:08 Shutting down` when using the command `curl -X POST -d 'shutdown' http://127.0.0.1:8088/hash`
server local message has  'recieved'  misspelled in message.
5. Unofficial defect, may be testing environment, sometimes the server is not able to handle large client loads (300 clients) and sometimes it does. 

## Test Cases 
1. Happy Path - Process up to 100 simultaneous requests and returns the correct hash 
2. Zero Length password
3. Max Length Password 100 characters
4. Clean Shutdown - Completing any in-flight password requests
5. Shutdown returns 200 and empty response 
6. Get Status Should Accept No Data 
7. Get Status Should return JSON - total requests and average request response time. 
8. TODO: Invalid characters in password, pending clarifications on valid characters  
9. TODO: Although not a requirement, Job ID should be unique 
 

## Password Hashing Application Specification
The following is the requirement specification that was used in building the password hashing
application.  It describes what the application should do.

* When launched, the application should wait for http connections.
* It should answer on the PORT specified in the PORT environment variable.
* It should support three endpoints:
   * A POST to /hash should accept a password. It should return a job identifier immediately. It should then wait 5 seconds and compute the password hash. The hashing algorithm should be SHA512.
   * A GET to /hash should accept a job identifier. It should return the base64 encoded password hash for the corresponding POST request.
   * A GET to /stats  should accept no data.  It should return a JSON data structure for the total hash requests since the server started and the average time of a hash request in milliseconds.
* The software should be able to process multiple connections simultaneously.
* The software should support a graceful shutdown request. Meaning, it should allow any in-flight password hashing to complete, reject any new requests, respond with a 200 andshutdown.
* No additional password requests should be allowed when shutdown is pending.

## Interacting with the Password Hashing Application

You can interact/test the application using curl.  The following are examples that would/should
generate similar returns - the job identifier does not need to conform to a specification.

* Post to the /hash endpoint
`$ curl -X POST -H "application/json" -d '{"password":"angrymonkey"}' http://127.0.0.1:8088/hash`
> 42

* Get the base64 encoded password
`$ curl -H "application/json" http://127.0.0.1:8088/hash/1`
> zHkbvZDdwYYiDnwtDdv/FIWvcy1sKCb7qi7Nu8Q8Cd/MqjQeyCI0pWKDGp74A1g==

* Get the stats
`$ curl http://127.0.0.1:8088/stats`
> {"TotalRequests":3,"AverageTime":5004625}

* Shutdown
`$ curl -X POST -d 'shutdown' http://127.0.0.1:8088/hash`
> 200 Empty Response
