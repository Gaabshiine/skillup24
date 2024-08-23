from django.db import connection
from django.conf import settings
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote



def execute_query(query, params=None, fetchone=False, fetchall=False):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        if fetchone:
            row = cursor.fetchone()
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row)) if row else None 
        if fetchall:
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        connection.commit()


class BunnyStreamClient:
    def __init__(self):
        self.api_key = settings.BUNNY_STREAM_API_KEY
        self.library_id = settings.BUNNY_STREAM_LIBRARY_ID
        self.base_url = f'https://video.bunnycdn.com/library/{self.library_id}'
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'AccessKey': self.api_key,
        }

    def upload_video(self, collection, video_path, video_title):
        """
        Upload a video to Bunny.net Stream.
        :param collection: Collection name where video will be stored.
        :param video_path: Path to the video file on the local machine.
        :param video_title: Title of the video to be uploaded.
        :return: Response containing video ID and other details.
        """
        # Read video file
        with open(video_path, 'rb') as video_file:
            # Prepare upload URL
            url = f'{self.base_url}/videos'
            data = {
                'title': video_title,
                'collection': collection,
            }
            files = {
                'file': video_file
            }
            
            # Send POST request to upload the video
            response = requests.post(url, headers=self.headers, data=data, files=files)
            if response.status_code == 201:
                return response.json()
            else:
                raise Exception(f"Failed to upload video: {response.content}")

    def get_video_url(self, video_id):
        """
        Get the playable video URL.
        :param video_id: Video ID from Bunny.net.
        :return: Playable video URL.
        """
        return f"https://iframe.mediadelivery.net/play/{self.library_id}/{video_id}"

    def delete_video(self, video_id):
        """
        Delete a video from Bunny.net Stream.
        :param video_id: Video ID from Bunny.net.
        :return: Status of the deletion request.
        """
        url = f'{self.base_url}/videos/{video_id}'
        response = requests.delete(url, headers=self.headers)
        if response.status_code == 204:
            return True
        else:
            raise Exception(f"Failed to delete video: {response.content}")