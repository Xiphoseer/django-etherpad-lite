import re

class PadError(ValueError):
    pass

class PadBackend(object):
    """This is the abstract base class for all pad backends. It
    defines all the avaliable API commands, which will then be
    used by the pad manager. Any feature added to a specific backend
    should have a corresponding (no-op) implementation here
    """

    def sanitize_pad_name(self, name):
        name = name.lower()
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'\:+', '_', name)
        return name

    def is_online(self):
        """Checks wether this backed is currently online
        """
        return True

    def get_or_create_group(self, mapper):
        """Creates the group in the backed
        """
        return mapper

    def delete_group(self, group_id):
        pass

    def create_group_pad(self, groupid, padname):
        """Creates a pad within a group
        """
        return ":".join([groupid, self.sanitize_pad_name(padname)])

    def list_group_pads(self, group_id):
        return []

    def set_password(self, padid, password):
        return False

    def set_public_status(self, padid, status):
        return True

    def delete_pad(self, padid):
        return False

    def is_pad_public(self, padid):
        return True

    def create_session(self, groupid, authorid, expires):
        return None

    def delete_session(self, sessionid):
        pass

    def create_user(self, user_id, name=None):
        return user_id

    def get_pad_link(self, pad_id):
        return None

    def get_text(self, pad_id):
        return None