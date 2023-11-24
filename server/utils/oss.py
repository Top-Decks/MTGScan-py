import os
import oss2
from datetime import datetime
from pathlib import Path
import base64
from io import BytesIO


class OSSUtil:
    def __init__(self):
        access_key_id = os.environ.get('OSS_ACCESS_KEY_ID')
        access_key_secret = os.environ.get('OSS_ACCESS_KEY_SECRET')
        self.endpoint = os.environ.get('OSS_ENDPOINT')
        self.bucket_name = os.environ.get('OSS_BUCKET_NAME')
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)

    def upload_img(self, img):
        try:
            filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".png"
            # tmp file path
            filepath = f"/tmp/scan_result/{filename}"
            # make sure tmp dir exists
            Path("/tmp/scan_result").mkdir(parents=True, exist_ok=True)
            # save image to file
            with open(filepath, "wb") as f:
                f.write(img)
            self.bucket.put_object_from_file(
                f"scan_result/{filename}", filepath)
            url = f'https://{self.bucket_name}.{self.endpoint}/scan_result/{filename}!q_30.jpg'
            print(f'scan result img url: {url}')
            return url
        except Exception as e:
            print("OSS Server Error")
            print(e)
            return ''

    def download_file(self, remote_path):
        remote_object = self.bucket.get_object(remote_path)
        return remote_object.read()

    def delete_file(self, remote_path):
        self.bucket.delete_object(remote_path)

    def list_files(self):
        files = []
        for object_info in oss2.ObjectIterator(self.bucket):
            files.append(object_info.key)
        return files
