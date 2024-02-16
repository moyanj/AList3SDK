class AListFolder:
    def __init__(self, path, init):
        # print(init)
        self.path = path
        self.provider = init['provider']
        self.size = init['size']
        self.modified = init['modified']
        self.created =init['created']
        
    def __str__(self):
        return self.path