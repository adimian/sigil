import blinker

signals = blinker.Namespace()

user_registered = signals.signal("user-registered")
user_request_password_recovery = signals.signal('user-request-password-recovery')
password_recovered = signals.signal("password-recovered")
user_login = signals.signal('user-login')
