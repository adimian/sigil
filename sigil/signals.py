import blinker

signals = blinker.Namespace()

user_registered = signals.signal("user-registered")

user_validated = signals.signal("user-validated")
