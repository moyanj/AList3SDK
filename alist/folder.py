class AListFolder:
    '''
    AList文件夹
    '''
    def __init__(self, path:str, init:dict):
        '''
        初始化
        
        Args:
            path (str):文件夹路径
            init (dict):初始化字典
            
        
        '''
        self.path = path
        self.provider = init["provider"]
        self.size = init["size"]
        self.modified = init["modified"]
        self.created = init["created"]

    def __str__(self):
        return self.path
