from alist import AList, AListUser

app = AListAdmin("http://127.0.0.1:5244/")
adm = AListUser("admin", "jdc20101217")
print(app.UserInfo())
print(app.headers)
