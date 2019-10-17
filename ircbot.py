#!/usr/bin/env python3

import datetime
import socket
import time
import ssl
import re
import random
import sys
import subprocess as sp

def runsh(command):
    pr = sp.Popen(command, shell=True, stdout=sp.PIPE)
    pr.wait()
    stdout = pr.stdout.read().decode()
    return stdout

class IRCBot:

    ERROR_RE = re.compile(r'^ERROR.*')
    PING_RE = re.compile(r'^PING.*')
    ENDMOTD_RE = re.compile(r'.*:End of /MOTD.*')
    ENDJOIN_RE = re.compile(r'.*:End of /NAMES.*')
    BOTCMD_re = r'^.*{channel}.*:!(.*)|^.*{channel}.*:.*([Cc]offee).*'

    GREETINGS = [
        'IT\'s YA BOI; BOT',
        'HOLLA',
        'HI',
        'HELLO HUMAN',
        'WHAT ARE THE HAPPY HAPS?'
    ]

    def __init__(self, *, nick='CPE_Bot', port=None, host=None):
        self.nick = nick
        self.port = port
        self.host = host
        self.sock = 0
        self.channel = None

        
    def __repr__(self):
        return f'IRCBot(nick={self.nick}, port={self.port}, host={self.host})'

    
    def connect(self):
        print(f'{self} IS CONNECTING...')
        self.sslcontext = ssl.SSLContext()
        self.sslcontext.load_verify_locations('/home/chris/.irssi/server.cert.pem')
        self.sock = self.sslcontext.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=self.host)
        self.sock.connect((self.host, self.port))
        self.send_cmd(f'NICK {self.nick}\n')
        self.send_cmd(f'USER {self.nick} 0 * :bot\n')

        while True:
            s = self.sock.recv(2048)
            s = s.decode().strip('\n\r')
            self.handle_message(s)
            if self.ENDMOTD_RE.match(s):
                break
            
        print(f'{self} HAS CONNECTED')

    def get_props(self):
        rv = dict()
        rv['channel'] = self.channel
        rv['host'] = self.host
        rv['port'] = self.port
        return rv


    def join_channel(self, channel):
        print(f'{self} IS JOINING CHANNEL {channel}...')
        self.channel = channel
        self.send_cmd(f'JOIN {channel}\n')

        s = 'notblank'
        while True:
            s = self.sock.recv(2048)
            s = s.decode().strip('\n\r')
            self.handle_message(s)
            if self.ENDJOIN_RE.match(s):
                break
            
        print(f'BOT HAS JOINED CHANNEL {channel}')
        self.greet()

        
    def send_cmd(self, command):
        '''Send command to server'''
        
        if command[-1] != '\n':
            command += '\n'
        self.sock.send(command.encode())

        
    def send_msg(self, msg, to=None):
        '''Send message to server; send sequentially if message is a list'''
        
        if to is None:
            to = self.channel

        print(f'{self} IS SENDING A MESSAGE TO {to}: \'{msg}\'')

        if isinstance(msg, list):
            for line in msg:
                self.send_msg(line, to)
            return
        
        self.send_cmd(f'PRIVMSG {to} {msg}')

        
    def greet(self):
        '''Choose a greeting from the self.GREETINGS list, and message the channel'''
        self.send_msg(random.choice(self.GREETINGS))


    def handle_message(self, s):
        '''
        In running the bot, input is monitored from users for a command or
        keyword. 
        '''
        
        if self.ERROR_RE.match(s):
            raise Exception(f'Something went wrong:\n{s}')
        
        if self.PING_RE.match(s):
            self.send_cmd(s.replace('PING', 'PONG'))
            return

        m = re.match(self.BOTCMD_re.format(**self.get_props()), s)
        if m:
            group = [g for g in m.groups() if g][0]
            botcommand = group.strip()
            self.handle_botcommand(botcommand)

            
    def handle_botcommand(self, c):
        if c in ['hi', 'hello', 'hey']:
            self.greet()
        elif c == 'fortune':
            fortune = runsh('fortune news')
            fortune = fortune.replace('\t', '  ').split('\n')
            self.send_msg(fortune)
        elif c == 'help':
            message = [
                'HELP HUMAN? OK.',
                'Commands:',
                '\'!hello\' -- bot responds with greeting',
                '\'!fortune\' -- bot will respond with a message/quote',
                '\'!help\' -- show this help'
            ]
            self.send_msg(message)
        elif c.lower() == 'coffee':
            self.send_msg('COFFEE!')

    def run(self):
        buf = str()
        while True:
            try:
                buf += self.sock.recv(2048).decode('utf-8')
            except UnicodeDecodeError:
                continue
    
            lines = buf.split('\n')
            buf = lines.pop()
    
            for line in lines:
                self.handle_message(line)

            
bot = IRCBot(host='130.159.42.114', port=6697)
bot.connect()
bot.join_channel('#general' if '--testing' not in sys.argv else '#testing')
bot.run()
