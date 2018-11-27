

>>> import base64
>>> import pyotp
>>> s = 'Hello World'
>>> secret = base64.b32encode(s)
>>> totp = pyotp.TOTP(secret)
>>> token = totp.now()
>>> print token
>>>
