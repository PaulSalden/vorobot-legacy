# Provide basic IRC functionality for the QuakeNet IRC network.

from vorobot import Module
from random import choice
from datetime import datetime, timedelta

# assist function for retrieving nickname
def nick(prefix):
	return prefix.split("!")[0]

class quakenet(Module):
	def __init__(self, cmds, variables, settings):
		super(quakenet, self).__init__(cmds, variables, settings)
		if 'channels' not in self.variables: self.variables['channels'] = set()
		if 'channicks' not in self.variables: self.variables['channicks'] = {}
		if 'chanmodes' not in self.variables: self.variables['chanmodes'] = {}
		if 'IAL' not in self.variables: self.variables['IAL'] = {}
		self.last_auth_update = datetime.now()



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
		self.nick_response_extended(prefix, command, args)
	
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
		if self.is_admin(prefix):
			words = args[1].split()
			if len(words) == 4 and (words[0:3], words[3][0]) == (["go", "go", "join"], "#"):
				self.cmds.join(words[3])
				return
			elif len(words) == 3 and words[0:3] == ["go", "go", "part"]:
				self.cmds.part(args[0])
				return



	# customary functions

	def join_response(self, prefix, command, args):
		if nick(prefix) == self.variables['botnick']:
			self.variables['channels'].add(args[0])
			self.variables['channicks'][args[0]] = set()
			self.cmds.raw('MODE {}'.format(args[0]))
			self.cmds.who(args[0], 'n%uhna')
		else:
			if nick(prefix) not in self.variables['IAL']:
				if prefix[-19:] == '.users.quakenet.org':
					userhost = prefix.split('!')[1].split('@')
					auth = userhost[1].split('.')[0]
					self.variables['IAL'][nick(prefix)] = {
						'user': userhost[0],
						'host': userhost[1],
						'auth': auth
						}
				else:
					self.cmds.who(nick(prefix), 'n%uhna')
		self.variables['channicks'][args[0]].add(nick(prefix))

	def part_response(self, prefix, command, args):
		self.variables['channicks'][args[0]].remove(nick(prefix))
		if nick(prefix) == self.variables['botnick']:
			self.variables['channels'].remove(args[0])
			return
		if not [True for channel in self.variables['channels'] if
			nick(prefix) in self.variables['channicks'][channel]]:
			self.variables['IAL'].pop(nick(prefix), None)

	def kick_response(self, prefix, command, args):
		self.variables['channicks'][args[0]].remove(args[1])
		if args[1] == self.variables['botnick']:
			self.variables['channels'].remove(args[0])
		if not [True for channel in self.variables['channels'] if
			args[1] in self.variables['channicks'][channel]]:
			self.variables['IAL'].pop(args[1], None)

	def quit_response(self, prefix, command, args):
		if nick(prefix) == self.variables['botnick']:
			exit()
		for channel in self.variables['channels']:
			self.variables['channicks'][channel].discard(nick(prefix))
		self.variables['IAL'].pop(nick(prefix), None)

	def nick_response_extended(self, prefix, command, args):
		for channel in self.variables['channels']:
			if nick(prefix) in self.variables['channicks'][channel]:
				self.variables['channicks'][channel].remove(nick(prefix))
				self.variables['channicks'][channel].add(args[0])
		if nick(prefix) in self.variables['IAL']:
			self.variables['IAL'][args[0]] = self.variables['IAL'][nick(prefix)]
			del self.variables['IAL'][nick(prefix)]

	def raw_response(self, prefix, command, args):
		if command == '324':
			self.variables['chanmodes'][args[1]] = args[2]
			return
		if command == '353':
			for nick in args[-1].split():
				self.variables['channicks'][args[-2]].add(
					nick.replace('@','').replace('+',''))
			return
		if command == '354':
			if len(args) == 5:
				# store user, host and auth
				self.variables['IAL'][args[3]] = {
					'user': args[1],
					'host': args[2],
					'auth': args[4]
					}
			elif len(args) == 3:
				# update auth
				self.variables['IAL'][args[1]]['auth'] = args[2]
		if datetime.now() - self.last_auth_update > timedelta(minutes=15):
			authless = [nick for nick in self.variables['IAL'] if
				self.variables['IAL'][nick]['auth'] == '0']
			for i in range(0 ,len(authless), 10):
				self.cmds.who(','.join(authless[i:i+10]), 'n%na')
			self.last_auth_update = datetime.now()

	def mode_response(self, prefix, command, args):
		self.cmds.raw('MODE {}'.format(args[0]))



	# assist function for checking if prefix belongs to admin
	def is_admin(self, prefix):
		return (nick(prefix) in self.variables['IAL'] and
			self.variables['IAL'][nick(prefix)]['auth'] == 'Voronoi')
