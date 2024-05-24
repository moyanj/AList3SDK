from alist import AList, AListUser

app = AListAdmin("http://127.0.0.1:5244/")
adm = AListUser("admin", "12r5jhdgchghjkrttjnbg6gxnkuufj[p8tcr8ufyy")
print(app.UserInfo())
print(app.headers)
