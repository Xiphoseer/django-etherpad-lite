import requests, re, json
from .base import PadBackend, PadError
from urllib.parse import urlparse

def clean_url(url):
    return url[:-1] if (url[-1:] == '/') else url

class HackMDBackend(PadBackend):

    def __init__(self, api_key, url):
        self.url = clean_url(url)
        self.session = requests.session()
        if api_key:
            if api_key.startswith('ldap:'):
                parts = api_key[5:].split(':', 1)
                if len(parts) == 2:
                    data = {'username': parts[0], 'password': parts[1]}
                    try:
                        self.session.post("/".join([self.url, 'auth', 'ldap']), data=data)
                    except Exception as e:
                        raise PadError("Could not connect to server")
                else:
                    raise ValueError("API-Key has to be 'username:password'", parts)
            else:
                raise ValueError("Authentication method not recognized")
        try:
            self.session.get(self.url)
        except Exception as e:
            raise PadError("Could not connect to server")

    def get_pad_link(self, pad_id, user_id):
        # ?view / ?edit / ?both
        return "".join(["/".join([self.url, pad_id]), "?both"])

    def create_group_pad(self, group_id, pad_name, text=None):
        if not text:
            text = "# {0}".format(pad_name)
        response = self.session.post("/".join([self.url, "new"]), data=text.encode('utf-8'), headers={'Content-Type': 'text/markdown'})
        pad_id = response.url.split('/')[-1]
        return pad_id

    def get_text(self, pad_id):
        # socket_io = "/".join([self.url, 'socket.io', "?noteId={0}&EIO=3&transport=polling".format(pad_id)])

        download_url = "/".join([self.url, pad_id, 'download'])
        response = self.session.get(download_url)
        return response.text

        # io = response.cookies['io']
        # print(response.cookies)
        # print(io)
        # data = re.sub(r'^\d+:\d+', '', response.text)
        # login = json.loads(data)
        # session_id = login['sid']
        # socket_io += "&sid=" + session_id
        # cookies = dict(io=io)

        # txt = ''
        # while txt == '':
        #     response = self.session.get(socket_io)
        #    txt = response.text
        #    if txt.startswith('2:40'):
        #        txt = txt[4:]


        # data = re.split(r'\d+:\d+', txt)
        # doc = [json.loads(dat) for dat in data if dat != '']

        # return doc[0][1]['str']
