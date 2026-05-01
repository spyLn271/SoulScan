class TerminateSignal(Exception): pass

def sigterm_handler(signum, frame):
    raise TerminateSignal("SIGTERM received")