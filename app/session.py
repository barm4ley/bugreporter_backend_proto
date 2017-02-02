
class Session(object):
    def __init__(self, sid):
        self.sid = sid
        self.filename = ''
        self.checksum = 0
        self.upload_status = -1
