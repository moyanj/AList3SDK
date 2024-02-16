import requests  as _req
class AListFile:
    def __init__(self, path, init):
        print(init)
        self.path = path
        self.name = init['name']
        self.provider = init['provider']
        self.size = init['size']
        self.modified = init['modified']
        self.created =init['created']
        self.url = init['raw_url']
        self.sign = init['sign']
    def __len__(self):
        return self.size
        
    def __str__(self):
        return self.path
        
    def __enter__(self):
        return self
    
    def __exit__(self,exc_type, exc_value, exc_tb):
        pass
        
    def read(self):
        return _req.get(self.url).content
        
    def save(self,path):
        r = _req.get(self.url)
        with open(path,'wb') as f:
            f.write(r.content)