# Assignment
This project holds the test cases and test automation for the Assignment
H. Wilson, September 2020 

## Password Hashing Application Specification
The following is the requirement specification that was used in building the password hashing
application.  It describes what the application 	should  do.

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
`$ curl -X POST -H "application/json" -d '{"password":"angrymonkey"}'`
http://127.0.0.1:8088/hash
> 42
* Get the base64 encoded password
`$ curl -H "application/json" http://127.0.0.1:8088/hash/1`
> zHkbvZDdwYYiDnwtDdv/FIWvcy1sKCb7qi7Nu8Q8Cd/MqjQeyCI0pWKDGp74A1g==
* Get the stats
$ curl 	http://127.0.0.1:8088/stats
> {"TotalRequests":3,"AverageTime":5004625}
* Shutdown
`$ curl -X POST -d ‘shutdown’ http://127.0.0.1:8088/hash`
> 200 Empty Response
