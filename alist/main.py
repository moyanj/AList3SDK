# pylint:disable=W0707
from hashlib import sha256 as _sha256
import requests as _req
from urllib.parse import urljoin as _urljoin
import json as _json
from sys import version_info as _version_info
from platform import platform as _pf
from . import Error, file, folder
from os.path import join as _pathjoin
from urllib.parse import quote as _quote
from typing import Union as _Union
from urllib3.filepost import encode_multipart_formdata
from os.path import dirname as _dirname
from os.path import basename as _basename
class AList:
    def __init__(self, endpoint: str):
        '''
        AList SDK, this is the main class.
        AList的SDK，此为主类。
        '''
        if "http" not in endpoint:
            raise ValueError(endpoint + "不是有效的uri")

        self.endpoint = endpoint
        self.user = object()

        ver = [
            str(_version_info.major),
            str(_version_info.minor),
            str(_version_info.micro),
        ]
        ver = ".".join(ver)
        pf = _pf().split("-")
        self.headers = {
            "User-Agent": f"AListSDK/1.0 (Python{ver};{pf[3]}) {pf[0]}/{pf[1]}",
            "Content-Type": "application/json",
            "Authorization": "",
        }

    def _isBadRequest(self, r, msg):
        try:
            j = _json.loads(r.text)
        except _json.JSONDecodeError:
            raise ValueError("服务器返回数据不是JSON数据")
        if j["code"] != 200:
            raise Error.ServerError(msg+':'+j['message'])
        
    def _getURL(self,path):
        return _urljoin(self.endpoint,path)
    def login(self, username: str, password: str, otp_code: str = None):
        '''
        Sign in
        登录
        Parameters:
            username:str - User name for AList(AList的用户名)
            password:str - Password for AList(AList的密码)
            otp_code:str - OTP code
        Returns:
            A Boolean value indicating whether the login was successful.
            一个布尔值，代表是否登录成功。
        Raises:
            AuthenticationError: Login failed
        '''
        
        URL = _urljoin(self.endpoint, "/api/auth/login/hash")
        
        # 对密码进行sha256摘要
        sha = _sha256()
        sha.update(password.encode())
        sha.update(b"-https://github.com/alist-org/alist")
        sha256Password = sha.hexdigest()
        # 构建json数据
        data = {"username": username, "password": sha256Password, "otp_code": otp_code}
        data = _json.dumps(data)
        
        r = _req.post(URL, headers=self.headers, data=data)
        # 处理返回数据
        self._isBadRequest(r,"账号或密码错误")
        # 保存
        self.user = _json.loads(r.text)["data"]["token"]
        self.headers["Authorization"] = self.user
        return True

    def userInfo(self):
        '''
        Get information about the currently logged on user.
        获取当前登录的用户的信息
        Parameters:
            Unused parameter
        Returns:
            A dictionary that contains information about the current user.
            一个字典，包含了当前用户的信息。
        Raises:
            No.
        '''  
              
        URL = _urljoin(self.endpoint, "/api/me")
        r = _req.get(URL, headers=self.headers)
        return r.json()["data"]

    def listdir(
        self,
        path: _Union[str,folder.AListFolder],
        page: int = 1,
        per_page: int = 50,
        refresh: bool = False,
        password: str = "",
    ):
        '''
        Lists all files or folders in the specified directory.
        列出指定目录下的所有文件或文件夹。
        Parameters:
            path:str,AListFolder - Directories to be listed(需要列出的目录)
            page:int = 1- Number of pages(页数)
            per_page:int = 50 - Quantity per page(每页的数量)
            refresh:bool = False - Whether to force a refresh(是否强制刷新)
            password:str = '' - Directory Password(目录密码)
 
        Returns:
            A generator that is a file in a specified directory.
            一个生成器，是指定目录下的文件。
        Raises:
            FileNotFoundError: The folder to be listed does not exist.
        '''
        
        URL = _urljoin(self.endpoint, '/api/fs/list')
        
        data = _json.dumps({
           "path": str(path),
           "password": password,
           "page": page,
           "per_page": per_page,
           "refresh": refresh
        })
        r = _req.post(URL,data=data, headers=self.headers)
        self._isBadRequest(r, '上传失败')
            
        for item in _json.loads(r.text)['data']['content']:
            i = {
                'path':_pathjoin(str(path), item['name']),
                'is_dir':item['is_dir']
            }
            yield i
            
       
    def open(self, path:_Union[str,folder.AListFolder,file.AListFile],password:str=''):
        URL = _urljoin(self.endpoint, '/api/fs/get')
        data = _json.dumps({
            'path':str(path),
            'password':password
        })
        r = _req.post(URL, headers=self.headers, data=data)
        r_json = _json.loads(r.text)
        if r_json['data']['is_dir']:
            return folder.AListFolder(str(path), r_json['data'])
        else:
            return file.AListFile(str(path),r_json['data'])
            
    def mkdir(self,path):
        URL = _urljoin(self.endpoint, '/api/fs/mkdir')
        data = _json.dumps({
            'path':path
        })
        
        r = _req.post(URL, data=data, headers=self.headers)
        self._isBadRequest(r, '创建失败')
        
        return True
        
    def upload(self,path:_Union[str,file.AListFile],local:str):
        URL = _urljoin(self.endpoint, '/api/fs/put')
        
        files = open(local,'rb').read()
        FilePath = _quote(str(path))
        
        headers = self.headers.copy()
        headers['File-Path'] = FilePath
        headers['Content-Length'] = str(len(files))
        del headers['Content-Type']
        
        r = _req.put(URL,data=files,headers=headers)
        self._isBadRequest(r, '上传失败')
        return True
        
    def rename(self, src:_Union[str,folder.AListFolder,file.AListFile], dst:str):
        URL = _urljoin(self.endpoint, '/api/fs/rename')
        
        data = _json.dumps({
            'path':str(src),
            'name':dst
        })
        
        r = _req.post(URL,headers=self.headers, data = data)
        self._isBadRequest(r,'重命名失败')
        return True
        
    def remove(self, path:_Union[str,file.AListFile]):
        URL = _urljoin(self.endpoint,'/api/fs/remove')
        payload = _json.dumps({
            "names": [
                str(_basename(str(path)))
            ],
            "dir": str(_dirname(str(path)))
            
        })
        
        r = _req.post(URL,data=payload,headers=self.headers)
        self._isBadRequest(r,'删除失败')
        return True
        
    def removeFolder(self,path:_Union[str,folder.AListFolder]):
        URL = self._getURL('/api/fs/remove_empty_directory')
        data = _json.dumps({
            'src_dir':str(path)
        })
        r = _req.post(URL,data=data,headers=self.headers)
        self._isBadRequest(r,'删除失败')
        return True
     
    def copy(self,src:_Union[str,file.AListFile],dstDir:_Union[str,folder.AListFolder]):
        URL = self._getURL('/api/fs/copy')
        data = _json.dumps({
            "src_dir": _dirname(str(src)),
            "dst_dir": str(dstDir),
            "names": [
                _basename(str(src))
            ]
        })
        r = _req.post(URL,data=data,headers=self.headers)
        self._isBadRequest(r,'复制失败')
        return True
        
    def move(self,src:_Union[str,file.AListFile],dstDir:_Union[str,folder.AListFolder]):
        URL = self._getURL('/api/fs/move')
        data = _json.dumps({
            "src_dir": _dirname(str(src)),
            "dst_dir": str(dstDir),
            "names": [
                _basename(str(src))
            ]
        })
        r = _req.post(URL,data=data,headers=self.headers)
        self._isBadRequest(r,'移动失败')
        return True
    
        
    
      
