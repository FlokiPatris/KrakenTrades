import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# Load JSON key from environment
creds_json = json.loads(os.environ['GOOGLE_DRIVE_JSON_KEY'])

# Setup GoogleAuth with service account
gauth = GoogleAuth()
scope = ['https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
gauth.credentials = credentials

# Connect to Google Drive
drive = GoogleDrive(gauth)

# Download file
file_id = '1qWAkAYZTY3oZK-eK41F4Psuhdm4cAUub'
file = drive.CreateFile({'id': file_id})
file.GetContentFile('trades.pdf')
