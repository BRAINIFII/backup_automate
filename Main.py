import json
import os

os.system("pip3 install boto3 requests")

def create_script(data):

    full_script = '''# Script Version: 2.0
# Changelog: Updated zip method to avoid programmatic bugs

import calendar
import os
import shutil
import time
import traceback
import warnings
from datetime import date, datetime, timedelta

import boto3
import requests

warnings.filterwarnings('ignore')

ACCESS_ID = "'''+data['ACCESS_ID']+'''"
ACCESS_KEY = "'''+data['ACCESS_KEY']+'''"
S3_BUCKET_NAME = "'''+data['BUCKET_NAME']+'''"

date_format = '%d/%m/%Y %H:%M:%S'

session = boto3.session.Session()
client = session.client('s3',
                        region_name='eu2',
                        endpoint_url='https://eu2.contabostorage.com',
                        aws_access_key_id=ACCESS_ID,
                        aws_secret_access_key=ACCESS_KEY)

s3_resource = boto3.resource('s3',
                        region_name='eu2',
                        endpoint_url='https://eu2.contabostorage.com',
                        aws_access_key_id=ACCESS_ID,
                        aws_secret_access_key=ACCESS_KEY)

curr_date = date.today()
file_curr_date = str(date.today())

now = datetime.now()
dt_string = now.strftime(date_format)
day_name = calendar.day_name[curr_date.weekday()]

TIMEOUT_DELAY_MIN = 30
TIMEOUT_DELAY = 60 * TIMEOUT_DELAY_MIN

time_change = timedelta(minutes=TIMEOUT_DELAY_MIN)
TIMEOUT = now + time_change
TIMEOUT_TEXT = str(TIMEOUT.strftime(date_format))
day_name = calendar.day_name[curr_date.weekday()]

def slack_message(path_name,message):
    url = 'https://hooks.slack.com/services/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'

    headers = {
        'Content-Type': 'application/json'
    }
    myobj = {
        'text': path_name +' '+ message
    }
    myobj['embeds'] = [
        {
            'description' : path_name +' '+ message,
            'title' : path_name
        }
    ]
    x = requests.post(url, json = myobj, headers=headers)
    if x.status_code == 200 or x.status_code == 204:
        print(path_name +' '+ message)
        return True
    else:
        print(x.status_code)
        return ('Slack Webhook Error:',x.status_code)

def discord_message(path_name,message):

    url = 'https://discord.com/api/webhooks/1002224644096532661/GWzBWdnyXX3B-LStm3POV_vHtWWS82zbUgy0qrgNX0c05WoRDKXQjOdKfZI_3aqar3T1'

    headers = {
        'Content-Type': 'application/json'
    }
    myobj = {
        'text': path_name +' '+ message
    }
    myobj['embeds'] = [
        {
            'description' : path_name +' '+ message,
            'title' : path_name
        }
    ]
    x = requests.post(url, json = myobj, headers=headers)
    if x.status_code == 200 or x.status_code == 204:
        print(path_name +' '+ message)
        return True
    else:
        print(x.status_code)
        return ('Discord Webhook Error:',x.status_code)

def upload_file(bkp_folder_name,file_path, bucket, file_name):
    object_name = bkp_folder_name+'/' + file_name
    print('Uploading new zip to s3 (' + bucket+' : '+object_name+ '): ' +file_name)
    client.upload_file(file_path, bucket, object_name)

def bkp(name,directory_path,filename):
    try:
        print('Making new zip: ' + filename+'.zip')
        os.system('rm -rf '+directory_path+'/public_html/*.zip')
        os.system('cd '+directory_path+'/public_html && rm -rf *.tar')
        os.system('zip -r /backup/'+filename+'.zip '+directory_path)
        upload_file(name,'/backup/'+filename+'.zip', S3_BUCKET_NAME,filename+'.zip')
        print('Uploaded ' + filename +'.zip to s3 ('+S3_BUCKET_NAME+ ')')
        discord_message(name,'Backup Successful: Uploaded ' + filename + '.zip to s3 ('+S3_BUCKET_NAME+ ')')
        print('Deleting old file from local: '  + filename + '.zip')
        os.system('rm -rf /backup/'+filename+'.zip')
    except Exception as e:
        slack_message(name,'Backup Failed\\nError:' + e)

def bkp_gen(name,directory_path,bkp_folder_name):
    print('\\n'+dt_string+', '+day_name)
    filename = day_name+'_'+ name +'_backup'
    try:
        discord_message(name,'Backup initiated')
        print('Copying database')
        os.system('cp -fr /backup/mysql/daily /backup/daily/'+bkp_folder_name+'/mysql')
        bkp(name,directory_path,filename)
    except Exception as e:
        slack_message(name,'Backup Failed\\nError:' + e)
        discord_message(name,'Backup Failed\\nError:' + e)
        print(name,'Backup Failed\\nError:', e)
        print('Retrying after '+ str(TIMEOUT_DELAY_MIN) +' minutes which is at ' + TIMEOUT_TEXT)
        slack_message(name,' backup retrying after '+ str(TIMEOUT_DELAY_MIN) +' minutes which is at ' + TIMEOUT_TEXT)
        discord_message(name,' backup retrying after '+ str(TIMEOUT_DELAY_MIN) +' minutes which is at ' + TIMEOUT_TEXT)
        time.sleep(TIMEOUT_DELAY)
        bkp(name,directory_path,filename)

# bkp_gen(<zip_file name>,<backup folder path>,<main folder name>)

# bkp_gen('a1tbc','/backup/daily/atb','atb')



bkp_gen("'''+data['zip_name']+'''","'''+data['bkp_path']+'''","'''+data['main_folder_name']+'''")
    '''
    filename = "/backup/backup.py"
    f = open(filename, "w")
    f.write(full_script)
    f.close()

try:
    f = open("bkp_config.json")
    data = json.load(f)
    create_script(data)
    os.system("(crontab -l ; echo \""+ data['cron_conf'] +" /usr/bin/python3 /backup/backup.py >> /var/log/daily_backup.log 2>&1\")| crontab -")
except Exception as e:
    print('Abe bkp_config file nahi banaya hai -_-\n',e)