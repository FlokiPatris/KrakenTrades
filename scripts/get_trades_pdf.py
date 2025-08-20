import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

creds_json = json.loads(os.environ["GOOGLE_DRIVE_JSON_KEY"])
gauth = GoogleAuth()
gauth.credentials = gauth.credentials_from_service_account_info(creds_json)
drive = GoogleDrive(gauth)

file_id = "1qWAkAYZTY3oZK-eK41F4Psuhdm4cAUub"
file = drive.CreateFile({"id": file_id})
file.GetContentFile("trades.pdf")
