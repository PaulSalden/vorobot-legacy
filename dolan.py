from vorobot import Module
from random import choice, randint

# Assist functions for retrieving the nickname and user@host from a prefix
def nick(prefix):
	return prefix.split("!")[0]
def hostmask(prefix):
	return prefix.split("!")[1]

class dolan(Module):
	def __init__(self, cmds, variables, settings):
		super(dolan, self).__init__(cmds, variables, settings)

	# Response to the IRCd welcome message
	def welcome_response(self, prefix, command, args):
		# Store the bot's initial nickname
		self.variables['botnick'] = args[0]
	
	# Response to the "End of MOTD" message
	def end_of_motd_response(self, prefix, command, args):
		# Authenticate with the Q bot
		self.cmds.rawsend("AUTH %s %s" % (self.settings['qauth'],
			self.settings['qpasswd']))
		# Set the usermode for having a hidden hostmask
		self.cmds.rawsend("MODE %s +x" % self.variables['botnick'])
	
	# Response to a "nickname taken" message
	def nick_taken_response(self, prefix, command, args):
		# Try to claim an alternative nickname
		self.cmds.rawsend("NICK %s%c" % (args[1], choice("`_")))
	
	# Response to a nickname change
	def nick_response(self, prefix, command, args):
		# See if it is the bot who changed nickname and if so, update its stored nickname
		if nick(prefix) == self.variables['botnick']:
			# Update the stored bot nickname
			self.variables['botnick'] = args[0]
	
	# Response to a ping request
	def ping_response(self, prefix, command, args):
		# Respond to the request
		self.cmds.rawsend("PONG :%s" % args[0])

	# Response to the "hidden host set" message
	def hidden_host_response(self, prefix, command, args):
		# Join all stored channels
		self.cmds.rawsend("JOIN %s" % self.settings['channel'])	
	
	# Response to a private message
	def privmsg_response(self, prefix, command, args):
                if args[1] == "\001VERSION\001":
                    self.cmds.rawsend("NOTICE %s :\001VERSION accually is dolan\001" % nick(prefix))
		elif randint(1,100) == 1:
                    split1 = randint(1,len(nick(prefix))-2)
                    split2 = randint(split1+1,len(nick(prefix))-1)
                    falsenick = "".join((nick(prefix)[:split1], nick(prefix)[split2], nick(prefix)[split1+1:split2],
                        nick(prefix)[split1], nick(prefix)[split2+1:]))
	    	    self.cmds.rawsend("PRIVMSG %s :%s pls" % (args[0], falsenick), randint(1,3))
