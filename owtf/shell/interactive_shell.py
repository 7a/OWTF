#!/usr/bin/env python
'''
The shell module allows running arbitrary shell commands and is critical
to the framework in order to run third party tools. The interactive shell module allows non-blocking
interaction with subprocesses running tools or remote connections (i.e. shells)
'''

import subprocess

from owtf.lib.general import *
from owtf.shell import blocking_shell
from owtf.shell.async_subprocess import *


class InteractiveShell(blocking_shell.Shell):

    COMPONENT_NAME = "interactive_shell"

    def __init__(self):
        blocking_shell.Shell.__init__(self)  # Calling parent class to do its init part
        self.register_in_service_locator()
        self.Connection = None
        self.Options = None
        self.CommandTimeOffset = 'InteractiveCommand'

    def CheckConnection(self, AbortMessage):
        if not self.Connection:
            cprint("ERROR - Communication channel closed - %s" % AbortMessage)
            return False
        return True

    def Read(self, Time=1):
        Output = ''
        if not self.CheckConnection('Cannot read'):
            return Output
        try:
            Output = RecvSome(self.Connection, Time)
        except DisconnectException:
            cprint("ERROR: Read - The Communication channel is down!")
            return Output  # End of communication channel
        print Output  # Show progress on screen
        return Output

    def FormatCommand(self, Command):
        if "RHOST" in self.Options and 'RPORT' in self.Options:  # Interactive shell on remote connection
            return "%s:%s-%s" % (self.Options['RHOST'], self.Options['RPORT'], Command)
        else:
            return "Interactive - %s" % Command

    def Run(self, Command, PluginInfo):
        Output = ''
        Cancelled = False
        if not self.CheckConnection("NOT RUNNING Interactive command: %s" % Command):
            return Output
        # TODO: tail to be configurable: \n for *nix, \r\n for win32
        LogCommand = self.FormatCommand(Command)
        CommandInfo = self.StartCommand(LogCommand, LogCommand)
        try:
            cprint("Running Interactive command: %s" % Command)
            SendAll(self.Connection, Command + "\n")
            Output += self.Read()
            self.FinishCommand(CommandInfo, Cancelled, PluginInfo)
        except DisconnectException:
            Cancelled = True
            cprint("ERROR: Run - The Communication Channel is down!")
            self.FinishCommand(CommandInfo, Cancelled, PluginInfo)
        except KeyboardInterrupt:
            Cancelled = True
            self.FinishCommand(CommandInfo, Cancelled, PluginInfo)
            Output += self.error_handler.user_abort('Command', Output)  # Identify as Command Level abort
        if not Cancelled:
            self.FinishCommand(CommandInfo, Cancelled, PluginInfo)
        return Output

    def RunCommandList(self, CommandList, PluginInfo):
        Output = ""
        for Command in CommandList:
            if Command != 'None':
                Output += self.Run(Command, PluginInfo)
        return Output

    def Open(self, Options, PluginInfo):
        Output = ''
        if not self.Connection:
            Name, Command = Options['ConnectVia'][0]
            self.Connection = AsyncPopen(Command, shell=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT,
                                         stdin=subprocess.PIPE,
                                         bufsize=1)
            self.Options = Options  # Store Options for Closing processing and if initial Commands are given
            if Options['InitialCommands']:
                Output += self.RunCommandList([Options['InitialCommands']], PluginInfo)
            Output += self.Read()
        Output += self.Read()
        return Output

    def Close(self, PluginInfo):
        print "wtf Close: %s" % str(self.Options)
        if self.Options['CommandsBeforeExit']:
            cprint("Running commands before closing Communication Channel..")
            self.RunCommandList(self.Options['CommandsBeforeExit'].split(self.Options['CommandsBeforeExitDelim']), PluginInfo)
        cprint("Trying to close Communication Channel..")
        self.Run("exit", PluginInfo)

        if self.Options['ExitMethod'] == 'kill':
            cprint("Killing Communication Channel..")
            self.Connection.kill()
        else:  # By default wait
            cprint("Waiting for Communication Channel to close..")
            self.Connection.wait()
        self.Connection = None

    def IsClosed(self):
        return self.Connection is None
