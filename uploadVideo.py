"""Take video File from Twitch Clips and Upload to YouTube + Add Thumbnail"""
import http.client
import random
import time
import httplib2

import google.oauth2.credentials
import google_auth_oauthlib.flow
# import googleapiclient.discovery
# import googleapiclient.errors
# from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

httplib2.RETRIES = 1

MAX_RETRIES = 10

RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = 'credentials.json'

SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          "https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

VALID_PRIVACY_STATUSES = ('public', 'private', 'unlisted')


def get_authenticated_service():
    try:
        credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(
            CLIENT_SECRETS_FILE)
    except ValueError as e:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES)
        credentials = flow.run_console()
        with open(CLIENT_SECRETS_FILE, 'w', encoding='utg-8') as file:
            file.write(credentials.to_json())
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def initialize_upload(youtube, options):
    tags = None
    if options['keywords']:
        tags = options['keywords'].split(',')

    body = dict(
        snippet=dict(
            title=options['title'],
            description=options['description'],
            tags=tags,
            categoryId=options['category']
        ),
        status=dict(
            privacyStatus=options['privacyStatus']
        )
    )

    insert_request = youtube.videos().insert(
        part=','.join(
            list(
                body.keys())),
        body=body,
        media_body=MediaFileUpload(
            options['file'],
            chunksize=-1,
            resumable=True))

    resumable_upload(insert_request, youtube)


def resumable_upload(request, youtube):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print('Uploading file...')
            status, response = request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print('Video id "%s" was successfully uploaded.' %
                          response['id'])
                    request = youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload('./output/thumbnail.png')
                    )
                    response = request.execute()
                    print(response)
                else:
                    exit(
                        'The upload failed with an unexpected response: %s' %
                        response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = 'A retriable HTTP error %d occurred:\n%s' % (
                    e.resp.status, e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = 'A retriable error occurred: %s' % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit('No longer attempting to retry.')

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print('Sleeping %f seconds and then retrying...' % sleep_seconds)
            time.sleep(sleep_seconds)


def startUpload(
        file,
        title='Test Title',
        description='Test Description',
        category=22,
        keywords='twitch, clips, germany, beste',
        privacyStatus='private'):
    youtube = get_authenticated_service()

    args = {
        'file': file,
        'title': title,
        'description': description,
        'category': category,
        'keywords': keywords,
        'privacyStatus': privacyStatus
    }
    print(args['file'])
    try:
        initialize_upload(youtube, args)
    except HttpError as e:
        print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
