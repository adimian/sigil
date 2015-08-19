import blinker

signals = blinker.Namespace()

user_registered = signals.signal("user-registered")
password_recovered = signals.signal("password-recovered")
user_login = signals.signal('user-login')
