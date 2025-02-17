import sys, time, os
from itertools import groupby
import disnake
from disnake.ext import commands
from config import Config
from babel import Babel


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class TpBot(commands.AutoShardedBot):
	"""this is the core of the merely framework."""
	config = Config()
	babel = Babel(config)
	verbose = False
	# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config['googlesheet']['credential']
	# print(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
 
	creds = None
	if os.path.exists('token.json'):
		creds = Credentials.from_authorized_user_file('token.json', config['googlesheet']['scope'])
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				config['googlesheet']['credential'], config['googlesheet']['scope'])
			creds = flow.run_local_server(port=0)
   # Save the credentials for the next run
		with open('token.json', 'w') as token:
			token.write(creds.to_json())

	def __init__(self, **kwargs):
    
		print(f"""
		technicalpoker framework{' beta' if self.config.getboolean('main', 'beta') else ''} v{self.config['main']['ver']}
		currently named {self.config['main']['botname']} by config, uses {self.config['main']['prefix_short']}
		created by Technicalpoker dev
		""")

		#stdout to file
		if not os.path.exists('logs'):
			os.makedirs('logs')
		sys.stdout = Logger()
		sys.stderr = Logger(err=True)

		if 'verbose' in kwargs:
			self.verbose = kwargs['verbose']

		# set intents
		intents = disnake.Intents.none()
		intents.guilds = self.config.getboolean('intents', 'guilds')
		intents.members = self.config.getboolean('intents', 'members')
		intents.bans = self.config.getboolean('intents', 'bans')
		intents.emojis = self.config.getboolean('intents', 'emojis')
		intents.integrations = self.config.getboolean('intents', 'integrations')
		intents.webhooks = self.config.getboolean('intents', 'webhooks')
		intents.invites = self.config.getboolean('intents', 'invites')
		intents.voice_states = self.config.getboolean('intents', 'voice_states')
		intents.presences = self.config.getboolean('intents', 'presences')
		intents.message_content = self.config.getboolean('intents', 'message_content')
		intents.messages = self.config.getboolean('intents', 'messages')
		intents.guild_messages = self.config.getboolean('intents', 'guild_messages')
		intents.dm_messages = self.config.getboolean('intents', 'dm_messages')
		intents.reactions = self.config.getboolean('intents', 'reactions')
		intents.guild_reactions = self.config.getboolean('intents', 'guild_reactions')
		intents.dm_reactions = self.config.getboolean('intents', 'dm_reactions')
		intents.typing = self.config.getboolean('intents', 'typing')
		intents.guild_typing = self.config.getboolean('intents', 'guild_typing')
		intents.dm_typing = self.config.getboolean('intents', 'dm_typing')

		super().__init__(
			command_prefix = self.check_prefix,
			help_command = None,
			intents = intents,
			case_insensitive = True
		)

		self.autoload_extensions()

	def check_prefix(self, _, msg:disnake.Message) -> list[str]:
		""" Check provided message should trigger the bot """
		if (
			self.config['main']['prefix_short'] and
			msg.content.lower().startswith(self.config['main']['prefix_short'].lower())
		):
			return (
				[msg.content[0:len(self.config['main']['prefix_short'])],
				msg.content[0 : len(self.config['main']['prefix_short'])] + ' ']
			)
		if (
			self.config['main']['prefix_long'] and
			msg.content.lower().startswith(self.config['main']['prefix_long'].lower())
		):
			return msg.content[0:len(self.config['main']['prefix_long'])] + ' '
		return commands.when_mentioned(self, msg)

	def autoload_extensions(self):
		""" Search the filesystem for extensions, list them in config, load them if enabled """
		# a natural sort is used to make it possible to prioritize extensions by filename
		# add underscores to extension filenames to increase their priority
		for ext in sorted(
			os.listdir('extensions'),
			key=lambda s:[int(''.join(g)) if k else ''.join(g) for k,
			g in groupby('\0'+s, str.isdigit)]
		):
			if ext[-3:] == '.py':
				extfile = ext[:-3]
				extname = extfile.strip('_')
				if extname in self.config['extensions'].keys():
					if self.config.getboolean('extensions', extname):
						try:
							self.load_extension('extensions.'+extfile)
							print(f"{extname} loaded.")
						except Exception as e:
							print(f"Failed to load extension '{ext[:-3]}':\n{e}")
					else:
						if self.verbose:
							print(f"{extname} is disabled, skipping.")
				else:
					self.config['extensions'][extname] = 'False'
					print(f"discovered {extname}, disabled by default, you can enable it in the config.")
		self.config.save()

class Logger(object):
	""" Records all stdout and stderr to log files, filename is based on date """
	def __init__(self, err=False):
		self.terminal = sys.stderr if err else sys.stdout
		self.err = err
	def write(self, message):
		""" Write output to log file """
		mfolder = os.path.join('logs', time.strftime("%m-%y"))
		if not os.path.exists(mfolder):
			os.makedirs(mfolder)
		self.terminal.write(message.encode('utf-8').decode('ascii','ignore'))
		fname = os.path.join(
			"logs",
			time.strftime("%m-%y"),
			"TpBot"+('-errors' if self.err else '')+"-"+time.strftime("%d-%m-%y")+".log"
		)
		with open(fname, "a", encoding='utf-8') as log:
			log.write(message)
	def flush(self):
		return self

if __name__ == '__main__':
	if set(['-h','--help']) & set(sys.argv):
		print("""
		TpBot commands
		-h,--help		shows this help screen
		-v,--verbose		enables verbose logging
		""")
	else:
		bot = TpBot(verbose=bool(set(['-v','--verbose']) & set(sys.argv)))

		token = bot.config.get('main', 'token', fallback=None)
		if token is not None:
			bot.run(token)
			
		else:
			raise Exception("failed to login! make sure you filled the token field in the config file.")

print("exited.")
