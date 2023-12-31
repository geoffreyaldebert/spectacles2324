from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from requests import HTTPError

import os
from dotenv import load_dotenv
load_dotenv()

from datetime import date
import dateutil.relativedelta

today = date.today()
alert_date = str(today + dateutil.relativedelta.relativedelta(days=62))
alert_date2 = str(today + dateutil.relativedelta.relativedelta(days=8))

secret_auth = os.getenv("SHEET_AUTH")
with open('secrets.json', 'w') as token:
    token.write(secret_auth)

token_auth = os.getenv("SHEET_TOKEN")
with open('token.json', 'w') as token:
    token.write(token_auth)


# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = os.getenv("SPECTACLE_SHEET")
SAMPLE_RANGE_NAME = 'spectacles!A2:J'

def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return
        message_content = "<html><head></head><body>"
        message_content += "<h2>Agenda Spectacle</h2>"
        urgences = ""
        next = ""
        for val in values:
            if val[7] == '' and val[6] != '' and val[6] <= alert_date2 and val[5] >= str(today):
                urgences += f"<div style='color: white; background-color: #5f75d4; padding: 15px; margin-bottom: 20px; border: 1px solid #ebebeb'><h2>{val[1]}</h2> (théâtre {val[0]})"
                urgences += f"<p>Metteur en scène : {val[3]} ; Auteur : {val[2]}</p>"
                if len(val[4].split('-')) > 2 and len(val[5].split('-')) > 2:
                    urgences += f"<p>Du : {val[4].split('-')[2]}/{val[4].split('-')[1]}/{val[4].split('-')[0]} Au : {val[5].split('-')[2]}/{val[5].split('-')[1]}/{val[5].split('-')[0]}</p>"
                if  len(val[6].split('-')) > 2:
                    urgences += f"<p>Ouverture des réservations : {val[6].split('-')[2]}/{val[6].split('-')[1]}/{val[6].split('-')[0]}</p>"
                urgences += f'<a href="{val[8]}">Plus d\'infos</a></div>'

            if val[7] == '' and val[4] <= alert_date and val[5] >= str(today):
                next += f"<div style='color: white; background-color: #de856a; padding: 15px; margin-bottom: 20px; border: 1px solid #ebebeb'><h2>{val[1]}</h2> (théâtre {val[0]})"
                next += f"<p>Metteur en scène : {val[3]} ; Auteur : {val[2]}</p>"
                if len(val[4].split('-')) > 2 and len(val[5].split('-')) > 2:
                    next += f"<p>Du : {val[4].split('-')[2]}/{val[4].split('-')[1]}/{val[4].split('-')[0]} Au : {val[5].split('-')[2]}/{val[5].split('-')[1]}/{val[5].split('-')[0]}</p>"
                next += f'<a href="{val[8]}">Plus d\'infos</a></div>'

        if urgences != "":
            message_content += "<h3><b>Urgence Résa</b>, ouverture des réservations dans les 7 prochains jours :</h3>"
            message_content += urgences
        if next != "":
            message_content += "<h3>Spectacle qui commencent <b>dans les deux prochains mois</b>, et dont les places ne sont pas encore réservées<h3>"
            message_content += next
        
        message_content += "</body></html>"
        
        if urgences != "" or next != "":
            service = build('gmail', 'v1', credentials=creds)
            
            message = MIMEMultipart('alternative')
            text = "Hi!\n"
            message['to'] = f'{os.getenv("RECIPIENT1")}, {os.getenv("RECIPIENT2")}'
            #message['to'] = os.getenv("RECIPIENT1")
            message['subject'] = f'Reminder Spectacles - {str(today)}'
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(message_content, 'html')
            message.attach(part1)
            message.attach(part2)
            create_message = {
                'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()
            }
            message = (service.users().messages().send(userId="me", body=create_message).execute())

    except HTTPError as error:
        print(F'An error occurred: {error}')
        message = None

    os.remove("secrets.json")
    os.remove("token.json")

if __name__ == '__main__':
    main()
