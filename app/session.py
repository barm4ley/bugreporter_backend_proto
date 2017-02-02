UPLOAD_STATUS_PENDING = 'pending'
UPLOAD_STATUS_FINISHED = 'finished'


class Session(object):
    def __init__(self, sid):
        self.sid = sid
        self.filename = ''
        self.checksum = 0
        self.last_chunk = -1
        self.status = UPLOAD_STATUS_PENDING
