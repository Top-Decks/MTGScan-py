import os
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class TXOSSUtil:
    def __init__(self):
        # 替换为用户的 SecretId，建议使用环境变量
        secret_id = os.environ.get('COS_SECRET_ID')
        # 替换为用户的 SecretKey，建议使用环境变量
        secret_key = os.environ.get('COS_SECRET_KEY')
        region = 'ap-beijing'
        self.bucket_name = 'topdeck-1258351289'

        # 检查环境变量是否都已设置
        if not all([secret_id, secret_key, region, self.bucket_name]):
            raise ValueError(
                "Missing Tencent COS environment variables (COS_SECRET_ID, COS_SECRET_KEY, COS_REGION, COS_BUCKET_NAME)")

        config = CosConfig(Region=region, SecretId=secret_id,
                           SecretKey=secret_key, Token=None, Scheme='https')  # 获取配置对象
        self.client = CosS3Client(config)

    def upload_img(self, img_bytes, content_type='image/png'):
        """
        上传图片数据到腾讯云 COS
        :param img_bytes: 图片的 bytes 数据
        :param content_type: 图片的 MIME 类型，默认为 image/png
        :return: 上传成功后的图片 URL，失败则返回空字符串
        """
        try:
            # 生成文件名和对象键名 (Key)
            file_extension = content_type.split(
                '/')[-1]  # 从 content_type 推断扩展名
            filename = datetime.now().strftime(
                "%Y%m%d%H%M%S") + f".{file_extension}"
            object_key = f"scan_result/{filename}"

            # 上传图片 bytes 数据
            response = self.client.put_object(
                Bucket=self.bucket_name,
                Body=img_bytes,
                Key=object_key,
                StorageClass='STANDARD',
                ContentType=content_type
                # EnableMD5=False # 可以根据需要启用 MD5 校验
            )

            # 检查上传是否成功 (put_object 成功时 response 为 ETag 等信息，失败会抛异常)
            logging.info(f"COS upload response: {response}")

            # 构建可访问的 URL (注意: 这需要存储桶是公共读或有相应的 CDN 配置)
            # 标准格式: https://<BucketName-APPID>.cos.<Region>.myqcloud.com/<Key>
            # 或者使用自定义域名
            # 这里使用标准格式，请确保 region 和 bucket_name 格式正确
            url = f'https://{self.bucket_name}.cos.{self.client.get_conf()._region}.myqcloud.com/{object_key}'

            # 腾讯云 COS 支持图片处理参数，类似阿里云 OSS 的 !q_30.jpg
            # 例如：?imageMogr2/format/jpg/quality/30
            # 这里暂时不加处理参数，如果需要可以添加
            # url += '?imageMogr2/format/jpg/quality/30'

            logging.info(f'Scan result img url: {url}')
            return url

        except Exception as e:
            logging.error("Tencent COS Server Error during upload")
            logging.exception(e)
            return ''

    def download_file(self, remote_path):
        """
        从腾讯云 COS 下载文件
        :param remote_path: 远端文件路径 (Key)
        :return: 文件内容的 bytes，失败则返回 None
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )
            # get_object 返回的是一个包含 'Body' 的字典，'Body' 是一个 StreamingBody 对象
            data = response['Body'].read()
            return data
        except Exception as e:
            logging.error(
                f"Tencent COS Server Error during download for {remote_path}")
            logging.exception(e)
            return None

    def delete_file(self, remote_path):
        """
        从腾讯云 COS 删除文件
        :param remote_path: 远端文件路径 (Key)
        :return: True 如果成功，False 如果失败
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )
            logging.info(
                f"Deleted {remote_path} from COS bucket {self.bucket_name}")
            return True
        except Exception as e:
            logging.error(
                f"Tencent COS Server Error during delete for {remote_path}")
            logging.exception(e)
            return False

    def list_files(self, prefix=''):
        """
        列出腾讯云 COS 存储桶中的文件
        :param prefix: 要列出的文件前缀，默认为空，列出所有文件
        :return: 文件键名 (Key) 的列表
        """
        files = []
        marker = ''
        while True:
            try:
                response = self.client.list_objects(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    Marker=marker
                    # MaxKeys=1000 # 可以指定每次列出的最大数量
                )
                if 'Contents' in response:
                    for content in response['Contents']:
                        files.append(content['Key'])

                if response.get('IsTruncated') == 'true':
                    marker = response.get('NextMarker')
                else:
                    break  # 已列出所有文件
            except Exception as e:
                logging.error("Tencent COS Server Error during list_files")
                logging.exception(e)
                break  # 出错时停止列举
        return files
