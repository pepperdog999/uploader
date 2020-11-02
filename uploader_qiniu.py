# -- coding: utf-8 --
# 未采用七牛提供的sdk，手动实现。

from sys import argv
import base64
import hmac
import json
import time
from datetime import datetime
from hashlib import sha1
import requests
import platform, os
from compat import b,s

_sys_info = '{0}; {1}'.format(platform.system(), platform.machine())
_python_ver = platform.python_version()

USER_AGENT = 'QiniuPython/{0} ({1}; ) Python/{2}'.format(
    '7.2.4', _sys_info, _python_ver)
_headers = {'User-Agent': USER_AGENT}
url = 'http://up-z2.qiniup.com/'


def urlsafe_base64_encode(data):
    ret = base64.urlsafe_b64encode(b(data))
    return s(ret)

def __token(data, sk):
    data = b(data)
    hashed = hmac.new(sk, data, sha1)
    return urlsafe_base64_encode(hashed.digest())

# 获取Token
def _get_token(bucket, ak, sk, expired_time=3600):
    data = {"scope": bucket}
    exp_time = int(time.time()) + expired_time
    data["deadline"] = exp_time
    data = json.dumps(data, separators=(',', ':'))
    encode = urlsafe_base64_encode(data)
    return ak + ":" + __token(encode, sk) + ":" + encode

# 流上传
def _put_file(token, k, path):
    fields = {}
    fields['key'] = k
    fields['token'] = token
    mime_type = 'application/octet-stream'
    file_name = os.path.basename(path)
    modify_time = int(os.path.getmtime(path))
    last_modified_date = datetime.utcfromtimestamp(modify_time)
    last_modified_str = last_modified_date.strftime(
        '%a, %d %b %Y %H:%M:%S GMT')
    fields['x-qn-meta-!Last-Modified'] = last_modified_str

    with open(path, 'rb') as input_stream:
        try:
            resp = requests.post(
                url, data=fields, files={'file': (file_name, input_stream, mime_type)}, headers=_headers)
            return resp.json()
        except Exception as e:
            return None

def upload(up_file_list=(), path=''):
    # 需要填写你的 Access Key 和 Secret Key
    access_key = 'NwsBONsRlNexKJcvlD32d2LK63dJgyKFKuCDU9eB'
    secret_key = 'q5l2A_amklbuM7Bw3T-ewvwoB7FyedkX6gDEeuTX'

    # 要上传的空间
    bucket_name = 'sagacity'
    # 生成上传 Token，可以指定过期时间等
    token = _get_token(bucket_name,access_key,secret_key)
    base_url = 'http://resource-sagacity.linestorm.ltd/'
    urls = list()

    for f in up_file_list:
        if not (os.path.exists(f)):
            print ('Upload Error:'+'文件不存在！')
            exit(-2)
        #上传后保存的文件名
        key = path + f.split("/")[-1]
        ret = _put_file(token, key, f)
        if ret is None or 'error' in ret:
            print('Upload Error:' + ret['error'])
            exit(-1)
        else:
            urls.append(base_url+ret['key'])
    print('Upload Success:')
    for url in urls: print(url)

if __name__ == "__main__":
    # 上传的文件列表
    uf = []
    # 默认上传的路径，可以通过 --path=file/ 参数指定路径
    path = 'img/'
    if len(argv) == 1:
        file = './resource/git-magic.png'
        uf.append(file)
    # elif len(argv) ==2 and argv[1].startswith('--'):
    #     print ('请指定文件！')
    #     exit(-2)
    elif len(argv)>2 and argv[1].startswith('--'): # 指定--path
        option = argv[1][2:]
        if(option.split('=')[0] == 'path'):
            path = option.split('=')[1]
        uf = argv[2:]
    else: #无参数的情况
        uf = argv[1:]
    upload(uf, path)