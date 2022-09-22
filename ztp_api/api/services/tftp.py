import datetime
from typing import Optional, Any
from ftplib import FTP
import io


class TftpWrapper:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.ftp = FTP(self.host, self.username, self.password)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()

    def start(self):
        self.ftp.connect()
        self.ftp.login(self.username, self.password)

    def finish(self):
        self.ftp.close()

    def list_files(self, folder=None):
        if folder:
            self.ftp.cwd(folder)
        result = self.ftp.nlst()
        return result

    def get_modify_time(self, filename: str, folder=None):
        if folder:
            self.ftp.cwd(folder)
        if filename not in self.ftp.nlst():
            raise FileNotFoundError
        response = self.ftp.voidcmd('MDTM {}'.format(filename))
        datetime_string = response[4:]
        return datetime.datetime.strptime(datetime_string, '%Y%m%d%H%M%S')

    def download(self, filename: str, folder=None):
        def store_one_line(line: bytes) -> None:
            decoded = line.decode('utf-8')
            data.append(decoded)
        if folder:
            self.ftp.cwd(folder)
        if filename not in self.ftp.nlst():
            raise FileNotFoundError
        data = []
        self.ftp.retrbinary('RETR {}'.format(filename), callback=store_one_line)
        file_content = ''.join(data)
        file_content = file_content.replace('\r', '')
        return file_content

    def upload(self, filename: str, content: str, folder=None):
        if folder:
            self.ftp.cwd(folder)
        file_obj = io.BytesIO(bytearray(content, 'utf-8'))
        self.ftp.storlines('STOR {}'.format(filename), file_obj)

    def upload_binary(self, filename: str, content: Any, folder=None):
        if folder:
            self.ftp.cwd(folder)
        file_obj = io.BytesIO(content)
        file_obj.flush()
        self.ftp.storbinary('STOR {}'.format(filename), file_obj)

    def delete(self, filename: str, folder=None):
        if folder:
            self.ftp.cwd(folder)
        if filename not in self.ftp.nlst():
            raise FileNotFoundError
        self.ftp.delete(filename)
