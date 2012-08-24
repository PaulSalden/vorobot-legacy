#!/usr/bin/env python
import socket
from ConfigParser import ConfigParser
from datetime import datetime, timedelta
from errno import EINPROGRESS
from select import select

# constants
BUFFER_RESERVE = len("SPLIDGEPLOIT\r\n")

# bot class
class Bot(object):
    # initialization
    def __init__(self, configfile):
        self.config = ConfigParser()
        self.config.read(configfile)
        self.settings = dict(self.config.items('settings'))

        self.in_buffer = ""
        self.out_buffer = ""
        self.out_queue = []

        self.process_queue = True
        self.bytes_buffered = 0
	
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(0)

        try:
            self.s.connect((self.settings['server'], int(self.settings['port'])))
            self.s.connect(('irc.quakenet.org', 6667))
        except socket.error, message:
            if message[0] != EINPROGRESS:
                raise
		
        self.cmds = Commands(self.out_queue)

        self.cmds.rawsend("USER %s * * :%s" % (self.settings['username'],
            self.settings['realname']))
	self.cmds.rawsend("NICK %s" % self.settings['desired_nick'])

        self.variables = {}
        self.modules = []
        for module in self.settings['modules'].split(','):
            if module in self.config.sections(): module_settings = dict(self.config.items(module))
            else: module_settings = {}
            new_module = __import__(module)
            self.modules.append(new_module.__dict__[module](self.cmds,
                self.variables, module_settings))

    # queue command to be sent
    def send(self, line, delay=0.0):
        target_time = datetime.now() + timedelta(seconds=delay) 
        self.out_queue.append((line, target_time))

    # fill and process input buffer
    def process_input(self):
        self.in_buffer = self.in_buffer + self.s.recv(8192)
        lines = self.in_buffer.split("\r\n")
        # leave unfinished lines in buffer
        self.in_buffer = lines.pop(-1)
	
        for line in lines:
            self.handle_line(line)

    # process output queue for sending
    def process_output(self):
        queue_remainder = []
        timeout = None
        while len(self.out_queue) > 0 and self.process_queue == True:
            time_left = self.out_queue[0][1] - datetime.now()
            time_left = time_left.total_seconds()
            # if command not to be sent yet, store for later
            if time_left > 0.0:
                if not timeout or time_left < timeout: timeout = time_left  
                queue_remainder.append(self.out_queue.pop(0))
                continue
            line = "%s\r\n" % self.out_queue[0][0]
            # interrupt processing once critical amount of bytes is sent
            if self.bytes_buffered + len(line) > 1024 - BUFFER_RESERVE:
                self.process_queue = False
                print "-> SPLIDGEPLOIT"
                self.out_buffer += "SPLIDGEPLOIT\r\n"
            else:
                print "->", self.out_queue.pop(0)[0]
                self.out_buffer += line
                self.bytes_buffered += len(line)
        self.out_queue.extend(queue_remainder)
        # return timeout to be used for select()
        return timeout

    # handle single incoming commands
    def handle_line(self, line):
        print "<-", line
        # split up comand line in (prefix, command, args)
        prefix = ''
        trailing = []
        if line[0] == ':': prefix, line = line[1:].split(' ', 1)
        if line.find(' :') != -1:
            line, trailing = line.split(' :', 1)
            args = line.split()
            args.append(trailing)
        else:
            args = line.split()
        command = args.pop(0)

        # deal with response to anti-flood check
        if len(args) > 1 and (command, args[1]) == ("421", "SPLIDGEPLOIT"):
            self.bytes_buffered = 0
            self.process_queue = True
            return

        # pass on command to modules
        for module in self.modules:
            module.raw_response(prefix, command, args)
            if command in module.COMMAND_HANDLERS:
                module.COMMAND_HANDLERS[command](prefix, command, args)


    # send as much of output buffer as possible
    def send_output(self):
        sent = self.s.send(self.out_buffer)
        self.out_buffer = self.out_buffer[sent:]

class Module(object):
    def __init__(self, cmds, variables, settings):
        self.cmds = cmds
        self.variables = variables
        self.settings = settings

        # define command handlers
        self.COMMAND_HANDLERS = {
            "001": self.welcome_response,
            "376": self.end_of_motd_response,
            "396": self.hidden_host_response,
            "433": self.nick_taken_response,
            "NICK": self.nick_response,
            "PING": self.ping_response,
            "PRIVMSG": self.privmsg_response,
    }

    def raw_response(self, prefix, command, args):
        pass

    def welcome_response(self, prefix, command, args):
        pass

    def end_of_motd_response(self, prefix, command, args):
        pass

    def hidden_host_response(self, prefix, command, args):
        pass

    def nick_taken_response(self, prefix, command, args):
        pass

    def nick_response(self, prefix, command, args):
        pass

    def ping_response(self, prefix, command, args):
        pass

    def privmsg_response(self, prefix, command, args):
        pass

class Commands(object):
    def __init__(self, out_queue):
        self.out_queue = out_queue

    def rawsend(self, line, delay=0.0):
        target_time = datetime.now() + timedelta(seconds=delay) 
        self.out_queue.append((line, target_time))

# example loop
if __name__ == "__main__":
    bots = []
    bots.append(Bot('vorobot.cfg'))

    while True:
        input = []
        output = []
        timeout = None

        for bot in bots:
            input.append(bot.s)
            bot_timeout = bot.process_output()
            if bot.out_buffer: output.append(bot.s)
            if bot_timeout and (not timeout or bot_timeout < timeout): timeout = bot_timeout

        inputready,outputready,exceptready = select(input,output,[],timeout)

        for bot in bots:
            if bot.s in outputready: bot.send_output()
            if bot.s in inputready: bot.process_input()
