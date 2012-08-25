# Provide basic IRC functionality for the QuakeNet IRC network.

from vorobot import Module
from random import choice

# assist functions for retrieving nickname and user@host from prefix
def nick(prefix):
	return prefix.split("!")[0]
def hostmask(prefix):
	return prefix.split("!")[1]

class quakenet(Module):
	def welcome_response(self, prefix, command, args):
		# store initial nick
		self.variables['botnick'] = args[0]
	
	def end_of_motd_response(self, prefix, command, args):
		# auth with Q
		self.cmds.rawsend("AUTH %s %s" % (self.settings['qauth'],
			self.settings['qpasswd']))
		# obtain hidden host
		self.cmds.rawsend("MODE %s +x" % self.variables['botnick'])
	
	def nick_taken_response(self, prefix, command, args):
		# claim alternative nick
		self.cmds.rawsend("NICK %s%c" % (args[1], choice("`_")))
	
	def nick_response(self, prefix, command, args):
		# if bot changes nick, store it
		if nick(prefix) == self.variables['botnick']:
			self.variables['botnick'] = args[0]
	
	def ping_response(self, prefix, command, args):
		self.cmds.rawsend("PONG :%s" % args[0])

	def hidden_host_response(self, prefix, command, args):
		# join channels
		self.cmds.rawsend("JOIN %s" % self.settings['channels'])	
	
	def privmsg_response(self, prefix, command, args):
                # provide CTCP version response
                if args[1] == "\001VERSION\001":
                    self.cmds.rawsend("NOTICE %s :\001VERSION accually is dolan\001" % nick(prefix))
