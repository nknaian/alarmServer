from socket import *
import random
import json

#Retrieve database info from database.txt, create vars for sub dicts
database = {}
with open('database.txt') as jsonFile:
    database = json.load(jsonFile)
userbase = database["userbase"] # Currently userbase holds emails, which are keys for passwords

#Setup server to receive messages on serverPort
serverPort = 9020
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(1)
print 'The server is ready to receive'

while 1:
    # Wait from a message from a client. Messages should come in json format
    connectionSocket, addr = serverSocket.accept()
    requestString = connectionSocket.recv(1024)
    print requestString

    # Initialize response object with empty string values and string (that will be sent) to ""
    responseDict = {"responseType": "", "responseData": ""}
    responseString = ""

    # Turn json string into dictionary
    requestDict = json.loads(requestString)

    # Parse dictionary into requestType and requestData
    if ("requestType" in requestDict) and ("requestData" in requestDict):
        requestType = requestDict["requestType"]
        requestData = requestDict["requestData"]
    else:
        responseDict["responseType"] = "INCORRECT JSON FORMAT FOR REQUEST"
        print responseDict["responseType"]
        break

    # Determine action to do based on requestType:

    if requestType == "auth_request":
        # Parse data dictionary into email and password
        if ("email" in requestData) and ("password" in requestData):
            email = requestData["email"]
            password = requestData["password"]
        else:
            responseDict["responseType"] = "INCORRECT JSON FORMAT FOR AUTH_REQUEST"
            print responseDict["responseType"]
            break

        # Check if the email is in the database.
        if email in userbase:
            # Check if password matches and set response to deny or allow access accordingly
            responseDict["responseType"] = "access denied"
            user = userbase[email]
            if password == user["password"]:
                responseDict["responseType"] = "access granted"

                # Set responseData to the username of the user logging in
                username = user["username"]
                responseData = {}
                responseData["username"] = username
                responseDict["responseData"] = responseData
        else:
            # Notify client of new user
            responseDict["responseType"] = "new user request"

    elif requestType == "username_verify_request":
        # Parse data dictionary into email, password, username
        if ("email" in requestData) and ("password" in requestData) and ("username" in requestData):
            email = requestData["email"]
            password = requestData["password"]
            username = requestData["username"]
        else:
            responseDict["responseType"] = "INCORRECT JSON FORMAT FOR USERNAME_VERIFY_REQUEST"
            print responseDict["responseType"]
            break

        # Search for the username
        duplicateUsernameFound = False
        for key in userbase:
            userEmail = userbase[key]
            if userEmail["username"] == username:
                duplicateUsernameFound = True
                break
        if duplicateUsernameFound:
            # Notify client that it must pick a different username
            responseDict["responseType"] = "username taken"
        else:
            # Build the dictionary to go in email
            emailDict = {}
            emailDict["username"] = username
            emailDict["password"] = password
            emailDict["alarmList"] = {}

            # Then add email dictionary to userbase
            userbase[email] = emailDict

            # Then save dictionary to json file
            with open('database.txt', 'w') as outfile:
                json.dump(database, outfile)

            # Notify client that the username is available so it can finish registration
            responseDict["responseType"] = "username available"

    elif requestType == "full_alarm_sync":
        #Get user email that is requesting full alarm list
        print requestData
        userEmail = requestData["email"]
        userEmailDict = userbase[userEmail]

        # If there are alarms, send them
        if userEmailDict["alarmList"]:
            responseDict["responseType"] = "alarms present"
            responseDict["responseData"] = userEmailDict["alarmList"]
        else:
            responseDict["responseType"] = "alarms absent"
            responseDict["responseData"] = ""

    elif requestType == "alarm_send":
        targetUser = requestData["targetUser"]
        url = requestData["url"]

        for key in userbase:
            userEmail = userbase[key]
            if userEmail["username"] == targetUser:
                if(userEmail["alarmList"] != ""):
                    userEmail["alarmList"] += ","
                userEmail["alarmList"] += url

                # Then save dictionary to json file
                with open('database.txt', 'w') as outfile:
                    json.dump(database, outfile)

    else:
        responseDict["responseType"] = "UNRECOGNIZED REQUEST"
        print responseDict["responseType"]
        break

    # Display and send response to client
    responseString = json.dumps(responseDict)
    print responseString
    connectionSocket.send(responseString)

    print 'Connection socket:', addr
    connectionSocket.close()
