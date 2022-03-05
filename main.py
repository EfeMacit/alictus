import os
from Google import Create_Service
import bot
from googleapiclient.http import MediaFileUpload
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
#Below are the initializations of the api services for drive and sheets
gauth = GoogleAuth()
drive = GoogleDrive(gauth)
CLIENT_SECRET_FILE = 'client_secrets.json'
API_NAME1 = 'drive'
API_VERSION1 = 'v3'
SCOPES1 = ['https://www.googleapis.com/auth/drive']
service1 = Create_Service(CLIENT_SECRET_FILE, API_NAME1, API_VERSION1, SCOPES1)
API_NAME2 = 'sheets'
API_VERSION2 = 'v4'
SCOPES2 = ['https://www.googleapis.com/auth/spreadsheets']
service2 = Create_Service(CLIENT_SECRET_FILE, API_NAME2, API_VERSION2, SCOPES2)

#Task1
#Getting folder name as an input from the user
folder_name=input("Please enter the folder name: ")
file_metadata = {
    'title': folder_name,
    'mimeType': 'application/vnd.google-apps.folder'
 }
file = drive.CreateFile(file_metadata)
file.Upload()
print('Folder ID: %s' % file.get('id'))
parent_id=file.get('id')
bot.notify_slack_channel("Folder created")#Slack nofitication
directory = "C:/Users/Efe/alictus/data"#root directory of the data which is in the excel format

#Uploading data to the google drive folder
for f in os.listdir(directory):
    filepath=os.path.join(directory,f)
    gfile=drive.CreateFile({'parents':[{'id':parent_id}], 'title':f})
    gfile.SetContentFile(filepath)
    bot.notify_slack_channel("Data uploaded")
    gfile.Upload()

#Task2
# method for converting excel file to the google sheets file
def convert_excel_file(file_path: str,folder_ids:list=None):
    file_metadata = {
        'name': 'data',
        'mimeType' : 'application/vnd.google-apps.spreadsheet',
        'parents':folder_ids
    }
    media=MediaFileUpload(filename=file_path,mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response = service1.files().create(media_body=media,body=file_metadata).execute()

    bot.notify_slack_channel("Data converted to spreadsheet format") #slack notification
    return response

for excel_file in os.listdir(directory):
    spreadsheet_id = convert_excel_file(os.path.join(directory,excel_file),[parent_id]).get('id') #getting spreadsheet id of data
mySpreadsheets = service2.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
response = service2.spreadsheets().values().get(spreadsheetId=spreadsheet_id, majorDimension='ROWS',
                                                range='A1:F14').execute()

rows = response['values'][0:][0:]
#Task3
#Creating seperated sheets for each campaign
for i in range(1, len(rows)):
    file_metadata = {
        'name': response['values'][i][0],
        'parents': [parent_id],
        'mimeType': 'application/vnd.google-apps.spreadsheet',
    }

    temp = float(response['values'][i][2]) * float(response['values'][i][4])#calculating total budget
    total_budget_value = [temp]#gets as a list
    new_sheet_file = service1.files().create(body=file_metadata).execute()#creating sheetfile for campaigns
    spreadsheet_id = new_sheet_file.get('id')
    service2.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    cell_range_insert = 'A1'
    total_budget = ['total budget']
    values = (
        (response['values'][0][0:] + total_budget),
        (response['values'][i][0:] + total_budget_value)
    )#inserting total budget and total budget value
    value_range_body = {
        'majorDimension': 'ROWS',
        'values': values
    }

    service2.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        valueInputOption='USER_ENTERED',
        range=cell_range_insert,
        body=value_range_body
    ).execute()

#method for calculating the budget campaign, this method calls from slackbot
def calculate_budget_campaign(campaign_name):
    global sheet_id
    query = f"parents='{parent_id}'"
    response = service1.files().list(q=query).execute()
    files = response.get('files')
    nextPageToken = response.get('nextPageToken')

    while nextPageToken:
        response = service1.files().list(orderBy='modifiedTime').execute() #sorting by modification time because deleted files existing
        files = extend(response.get('files'))
        nextPageToken = response.get('nextPageToken')
    for i in range(len(files)):
        if files[i].get('name') == campaign_name:#Couldnt find a getter version of get('name') hope it exists
            sheet_id = files[i].get('id')
            break
    response = service2.spreadsheets().values().get(spreadsheetId=sheet_id, majorDimension='ROWS',
                                                    range='A1:G2').execute()
    return response['values'][-1][-1]
