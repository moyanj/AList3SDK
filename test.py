from alist import AList
app = AList('http://file.moyanjdc.top/')
app.login('admin', 'jdc20101217')

app.remove('/百度网盘/2.txt')
print(app.headers)