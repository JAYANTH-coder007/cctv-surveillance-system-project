# -*- coding: utf-8 -*-
"""
Created on Sat Mar 27 10:16:00 2021

@author: INBOTICS
"""
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
   
# For using listdir()
import os
   
  
# Below code does the authentication
# part of the code
gauth = GoogleAuth()
# Try to load saved client credentials
gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
else:
    # Initialize the saved creds
    gauth.Authorize()
# Save the current credentials to a file
gauth.SaveCredentialsFile("mycreds.txt")

drive = GoogleDrive(gauth)
   
# replace the value of this variable
# with the absolute path of the directory
path = r"t1.mp4"   
   
# iterating thought all the files/folder
# of the desired directory
#for x in os.listdir(path):
   
f = drive.CreateFile({'title': 'testfile.mp4'})
f.SetContentFile(path)
f.Upload()
  
    # Due to a known bug in pydrive if we 
    # don't empty the variable used to
    # upload the files to Google Drive the
    # file stays open in memory and causes a
    # memory leak, therefore preventing its 
    # deletion
f = None