import blinker

signals = blinker.Namespace()

user_registered = signals.signal("user-registered")
user_validated = signals.signal("user-validated")
user_login = signals.signal('user-login')
user_logout = signals.signal('user-login')
