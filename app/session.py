UPLOAD_STATUS_PENDING = 'pending'
UPLOAD_STATUS_FINISHED = 'finished'


class Session(object):
    def __init__(self, sid):
        self.sid = sid
        self.filename = ''
        self.checksum = 0
        self.last_chunk = -1
        self.status = UPLOAD_STATUS_PENDING


class SessionsRepo(object):
    def __init__(self):
        self.sessions = {}

    def add(self, session):
        self.sessions[session.sid] = session

    def delete(self, sid):
        self.sessions.pop(sid, None)

    def get(self, sid):
        return self.sessions[sid]

    def is_known(self, sid):
        return sid in self.sessions
