import re

from urllib.error import HTTPError, URLError
from py_etherpad import EtherpadLiteClient

from . import base

def to_bool_str(val):
    return "true" if val else "false"

class EtherpadLiteBackend(base.PadBackend):

    def __init__(self, apikey, url):

        self.url = url[:-1] if (url[-1:] == '/') else url
        self.api = "/".join([self.url, "api"])
        self.epclient = EtherpadLiteClient(apikey, self.api)

    def sanitize_pad_name(self, name):
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r':+', '_', name)
        return name

    def is_online(self):
        try:
            self.epclient.checkToken()
            return True
        except HTTPError as e:
            return False
        except URLError as e:
            return False

    def get_or_create_group(self, mapper):
        try:
            result = self.epclient.createGroupIfNotExistsFor(mapper)
            return result['groupID']
        except Exception as e:
            raise base.PadError("Could not create pad group", e)

    def delete_group(self, group_id):
        try:
            self.epclient.deleteGroup(group_id)
            return True, group_id
        except ValueError as e:
            return False, str(e)

    def list_group_pads(self, group_id):
        result = self.epclient.listPads(group_id)
        return [pad.split('$')[1] for pad in result['padIDs']]

    def create_group_pad(self, groupid, padname, text=None):
        padid = "$".join([groupid, self.sanitize_pad_name(padname)])
        try:
            self.epclient.createGroupPad(groupid, padname)
            if text:
                self.epclient.setText(padid, text)
        except ValueError:
            pass
        return padid

    def set_password(self, padid, password):
        self.epclient.setPassword(self.padid,self.password)
        return True

    def set_public_status(self, padid, status):
        self.epclient.setPublicStatus(padid, to_bool_str(status)) # Sigh, pyEtherpadLite
        return status

    def delete_pad(self, padid):
        try:
            self.epclient.deletePad(padid)
            return True
        except ValueError:
            return False

    def is_pad_public(self, padid):
        result = self.epclient.getPublicStatus(padid)
        return result['publicStatus']

    def create_session(self, group_id, author_id, expires):
        result = self.epclient.createSession(group_id, author_id, str(expires))
        return result["sessionID"]

    def delete_session(self, session_id):
        self.epclient.deleteSession(session_id)

    def create_user(self, user_id, name=None):
        name = name or user_id
        result = self.epclient.createAuthorIfNotExistsFor(user_id, name)
        return result['authorID']

    def get_pad_link(self, pad_id, user_id):
        base = "/".join([self.url, "p", pad_id])
        return "".join([base, "?userName=", user_id]) if user_id else base

    def get_text(self, pad_id):
        text = self.epclient.getText(pad_id)
        return text['text']
