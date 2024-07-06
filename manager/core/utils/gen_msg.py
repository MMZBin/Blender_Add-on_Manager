class MsgType:
    INFO: str     = "Info"
    CAUTION: str  = "Caution"
    ERROR: str    = "Error"
    CRITICAL: str = "Critical"

@staticmethod
def gen_msg(sender: type, type: str, msg: str) -> str: return f'{sender.__name__}: {type}: {msg}' # type: ignore
