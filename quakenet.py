# Provide basic IRC functionality for the QuakeNet IRC network.

from vorobot import Module
from random import choice

# assist functions for retrieving nickname and user@host from prefix
def nick(prefix):
	return prefix.split("!")[0]

class quakenet(Module):
	def welcome_response(self, prefix, command, args):
		# store initial nick
		self.variables['botnick'] = args[0]
	
	def end_of_motd_response(self, prefix, command, args):
		# auth with Q
		self.cmds.raw("AUTH %s %s" % (self.settings['qauth'],
			self.settings['qpasswd']))
		# obtain hidden host
		self.cmds.mode(self.variables['botnick'], "+x")
	
	def nick_taken_response(self, prefix, command, args):
		# claim alternative nick
		self.cmds.nick("%s%c" % (args[1], choice("`_")))
	
	def nick_response(self, prefix, command, args):
		# if bot changes nick, store it
		if nick(prefix) == self.variables['botnick']:
			self.variables['botnick'] = args[0]
	
	def ping_response(self, prefix, command, args):
		self.cmds.raw("PONG :%s" % args[0])

	def hidden_host_response(self, prefix, command, args):
		# join channels
		self.cmds.join(self.settings['channels'])	
	
	def privmsg_response(self, prefix, command, args):
                # provide CTCP version response
                if args[1] == "\001VERSION\001":
                    self.cmds.notice(nick(prefix), "\001VERSION accually is dolan\001")
                    return
                # allow channel management
                if prefix == self.settings['admin_host']:
                    words = args[1].split()
                    if len(words) == 4 and (words[0:3], words[3][0]) == (["go", "go", "join"], "#"):
                        self.cmds.join(words[3])
                        return
                    elif len(words) == 3 and words[0:3] == ["go", "go", "part"]:
                        self.cmds.part(args[0])
                        return
