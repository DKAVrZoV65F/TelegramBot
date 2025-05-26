# handlers/__init__.py

def register_handlers(dp):
    from .common import register as _c
    from .admin import register as _a
    from .tag_actions import register as _t
    from .collector import register as _col
    _c(dp)
    _a(dp)
    _t(dp)
    _col(dp)
