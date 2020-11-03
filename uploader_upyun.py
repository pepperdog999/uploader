# -- coding: utf-8 --
# 未采用又拍云提供的sdk，手动实现。

from sys import argv
import base64
import hmac
import json
import time
from datetime import datetime
from hashlib import sha1,md5
import requests
import os
from compat import b,s,con

# 从配置文件读取
con.read("./resource/configure.ini")  # 文件名
_headers = {}
kwargs = {'allow-file-type': 'jpg,jpeg,png,py'}
host = 'http://v0.api.upyun.com'

def cur_dt():
    dt = datetime.utcnow()
    weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][dt.weekday()]
    month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
             'Oct', 'Nov', 'Dec'][dt.month - 1]
    return '%s, %02d %s %04d %02d:%02d:%02d GMT' % \
           (weekday, dt.day, month, dt.year, dt.hour, dt.minute, dt.second)
    return httpdate_rfc1123()

def urlsafe_base64_encode(data):
    ret = base64.urlsafe_b64encode(b(data))
    return s(ret)

def _make_policy(data):
    policy = json.dumps(data)
    return urlsafe_base64_encode(policy)

def _make_signature(**kwargs):
    signarr = [kwargs['method'], kwargs['uri'], kwargs['date']]
    if kwargs.get('policy'):
        signarr.append(kwargs['policy'])
    if kwargs.get('content_md5'):
        signarr.append(kwargs['content_md5'])
    signstr = '&'.join(signarr)
    # hashed = hmac.new(b(kwargs['password']), b(signstr), sha1)
    # return 'UPYUN %s:%s' % (kwargs['username'], urlsafe_base64_encode(hashed.digest()))
    signature = base64.b64encode(
        hmac.new(b(kwargs['password']), b(signstr),
                 digestmod=sha1).digest()
    ).decode()
    return 'UPYUN %s:%s' % (kwargs['username'], signature)


# 流上传
def _put_file(username, password, service, k, path, expired_time=1800):
    fields = {}
    exp_time = int(time.time()) + expired_time
    fields['expiration'] = exp_time
    fields['save-key'] = k
    fields['service'] = service
    fields['date'] = cur_dt()
    fields.update(kwargs)
    policy = _make_policy(fields)
    signature = _make_signature(
        username=username,
        password=(md5(b(password)).hexdigest()),
        method='POST',
        uri='/%s/' % service,
        date=cur_dt(),
        policy=policy
    )

    with open(path, 'rb') as input_stream:
        try:
            url = '%s/%s/' % (host, service)
            postdata = {
                'policy': policy,
                'authorization': signature,
                'file': (os.path.basename(os.path.basename(path)), input_stream),
            }
            resp = requests.post(url, files=postdata, headers=_headers)
            return resp.json()
        except Exception as e:
            return None

def upload(up_file_list=(), path=''):
    username = con.get('upyun', 'username')
    password = con.get('upyun', 'password')
    #要上传的空间
    service_name = con.get('upyun', 'service_name')
    base_url = con.get('upyun', 'base_url')
    urls = list()

    for f in up_file_list:
        if not (os.path.exists(f)):
            print ('Upload Error:'+'文件不存在！')
            exit(-2)
        #上传后保存的文件名
        key = '%s/%s' % (path, f.split("/")[-1])
        ret = _put_file(username, password, service_name, key, f)
        print (ret)
        if int(ret['code']) == 200:
            urls.append(base_url+ret['url'])
        else:
            print('Upload Error:' + ret['message'])
            exit(-1)
    print('Upload Success:')
    for url in urls: print(url)

if __name__ == "__main__":
    # 上传的文件列表
    uf = []
    # 默认上传的路径，可以通过 --path=file/ 参数指定路径
    path = con.get('DEFAULT', 'remote_path')
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