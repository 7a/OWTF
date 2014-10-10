#!/usr/bin/env python
"""

owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The core is the glue that holds the components together and allows some of them
to communicate with each other

"""

import os
import sys
import time
import signal
import socket
import logging
import multiprocessing
import subprocess

from framework.dependency_management.component_initialiser import ComponentInitialiser
from framework import timer, error_handler
from framework.config import config, health_check
from framework.db import db
from framework.http import requester
from framework.http.proxy import proxy, transaction_logger, tor_manager
from framework.plugin import worker_manager
from framework.protocols import smb
from framework.interface import server
from framework.lib.formatters import ConsoleFormatter, FileFormatter
from framework.selenium import selenium_handler
from framework.shell import interactive_shell
from framework.utils import FileOperations, catch_io_errors, OutputCleaner, OWTFLogger
from framework.wrappers.set import set_handler
from framework.lib.general import cprint
from framework.dependency_management.dependency_resolver import BaseComponent


class Core(BaseComponent):

    COMPONENT_NAME = "core"

    """
    The glue which holds everything together
    """
    def __init__(self, root_dir, owtf_pid, args):
        self.register_in_service_locator()
        """
        [*] Tightly coupled, cohesive framework components
        [*] Order is important

        + IO decorated so as to abort on any permission errors
        + Required folders created
        + All other components are attached to core: shell, db etc... (using ServiceLocator)
        """

        # ------------------------ IO decoration ------------------------ #
        self.decorate_io()

        # -------------------- Component attachment -------------------- #
        self.db = self.get_component("db")
        self.config = self.get_component("config")
        self.db_config = self.get_component("db_config")
        self.zest = self.get_component("zest")
        self.zap_api_handler = self.get_component("zap_api")
        self.error_handler = self.get_component("error_handler")

        # ----------------------- Directory creation ----------------------- #
        self.create_dirs()
        self.pnh_log_file()  # <-- This is not supposed to be here

        self.timer = self.get_component("timer")
        self.shell = self.get_component("shell")
        self.enable_logging()
        self.reporter = self.get_component("reporter")
        self.selenium = selenium_handler.Selenium()
        self.interactive_shell = interactive_shell.InteractiveShell()
        self.set = set_handler.SETHandler()
        self.smtp = self.get_component("smtp")
        self.smb = smb.SMB()

        # The following attributes will be initialised later
        self.plugin_helper = None
        self.tor_process = None
        self.requester = None

        # --------------------------- Init calls --------------------------- #
        # Nothing as of now
        self.health_check()

    def health_check(self):
        self.HealthCheck = health_check.HealthCheck()

    def create_dirs(self):
        """
        Any directory which needs to be created at the start of owtf
        needs to be placed inside here. No hardcoding of paths please
        """
        # Logs folder creation
        if not os.path.exists(self.config.FrameworkConfigGetLogsDir()):
            FileOperations.create_missing_dirs(self.config.FrameworkConfigGetLogsDir())
        # Temporary storage directories creation
        self.create_temp_storage_dirs()

    def create_temp_storage_dirs(self):
        """Create a temporary directory in /tmp with pid suffix."""
        tmp_dir = os.path.join('/tmp', 'owtf')
        if not os.path.exists(tmp_dir):
            tmp_dir = os.path.join(tmp_dir, str(self.config.OwtfPid))
            if not os.path.exists(tmp_dir):
                FileOperations.make_dirs(tmp_dir)

    def clean_temp_storage_dirs(self):
        """Rename older temporary directory to avoid any further confusions."""
        curr_tmp_dir = os.path.join('/tmp', 'owtf', str(self.config.OwtfPid))
        new_tmp_dir = os.path.join(
            '/tmp', 'owtf', 'old-%d' % self.config.OwtfPid)
        if os.path.exists(curr_tmp_dir) and os.access(curr_tmp_dir, os.W_OK):
            os.rename(curr_tmp_dir, new_tmp_dir)

    def pnh_log_file(self):
        self.path = self.config.FrameworkConfigGet('PNH_EVENTS_FILE')
        self.mode = "w"
        try:
            if os.path.isfile(self.path):
                pass
            else:
                with FileOperations.open(self.path, self.mode, owtf_clean=False):
                    pass
        except IOError as e:
            OWTFLogger.log("I/O error ({0}): {1}".format(e.errno, e.strerror))
            raise

    def write_event(self, content, mode):
        self.content = content
        self.mode = mode
        self.file_path = self.config.FrameworkConfigGet('PNH_EVENTS_FILE')

        if (os.path.isfile(self.file_path) and os.access(self.file_path, os.W_OK)):
            try:
                with FileOperations.open(self.file_path, self.mode, owtf_clean=False) as log_file:
                    log_file.write(self.content)
                    log_file.write("\n")
                return True
            except IOError:
                return False

    def get_child_pids(self, parent_pid):
        ps_command = subprocess.Popen(
            "ps -o pid --ppid %d --noheaders" % parent_pid,
            shell=True,
            stdout=subprocess.PIPE)
        output, error = ps_command.communicate()
        return [int(child_pid) for child_pid in output.readlines("\n")[:-1]]

    def GetCommand(self, argv):
        # Format command to remove directory and space-separate arguments.
        return " ".join(argv).replace(argv[0], os.path.basename(argv[0]))

    def Start_TOR_Mode(self, options):
        if options['TOR_mode'] is not None:
            if options['TOR_mode'][0] != "help":
                if tor_manager.TOR_manager.is_tor_running():
                    self.tor_process = tor_manager.TOR_manager(
                        self,
                        options['TOR_mode'])
                    self.tor_process = self.tor_process.Run()
                else:
                    tor_manager.TOR_manager.msg_start_tor(self)
                    tor_manager.TOR_manager.msg_configure_tor()
                    self.error_handler.FrameworkAbort("TOR Daemon is not running")
            else:
                tor_manager.TOR_manager.msg_configure_tor()
                self.error_handler.FrameworkAbort("Configuration help is running")

    def StartBotnetMode(self, options):
        ComponentInitialiser.intialise_proxy_manager(options)

    def StartProxy(self, options):
        ComponentInitialiser.initialisation_phase_3([self.db_config.Get('INBOUND_PROXY_IP'), self.db_config.Get('INBOUND_PROXY_PORT')])
        # The proxy along with supporting processes are started
        if True:
            # Check if port is in use
            try:
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_socket.bind((
                    self.db_config.Get('INBOUND_PROXY_IP'),
                    int(self.db_config.Get('INBOUND_PROXY_PORT'))))
                temp_socket.close()
            except socket.error:
                self.error_handler.FrameworkAbort(
                    "Inbound proxy address " +
                    self.db_config.Get('INBOUND_PROXY_IP') + ":" +
                    self.db_config.Get("INBOUND_PROXY_PORT") +
                    " already in use")

            # If everything is fine.
            self.ProxyProcess = proxy.ProxyProcess()
            self.ProxyProcess.initialize(
                options['OutboundProxy'],
                options['OutboundProxyAuth']
            )
            self.TransactionLogger = transaction_logger.TransactionLogger(
                cache_dir=self.db_config.Get('INBOUND_PROXY_CACHE_DIR')
            )
            logging.info(
                "Starting Inbound proxy at %s:%s",
                self.db_config.Get('INBOUND_PROXY_IP'),
                self.db_config.Get("INBOUND_PROXY_PORT"))
            self.ProxyProcess.start()
            logging.info("Starting Transaction logger process")
            self.TransactionLogger.start()
            self.plugin_helper = self.get_component("plugin_helper")
            self.requester = self.get_component("requester")
            logging.info(
                "Proxy transaction's log file at %s",
                self.db_config.Get("PROXY_LOG"))
            logging.info(
                "Interface server log file at %s",
                self.db_config.Get("SERVER_LOG"))
            logging.info(
                "Execution of OWTF is halted. You can browse through "
                "OWTF proxy) Press Enter to continue with OWTF")
        else:
            ComponentInitialiser.initialisation_phase_3(options['OutboundProxy'])
            self.requester = self.get_component("requester")


    def enable_logging(self, **kwargs):
        """
        + process_name <-- can be specified in kwargs
        + Must be called from inside the process because we are kind of
          overriding the root logger
        + Enables both file and console logging
        """
        process_name = kwargs.get(
            "process_name",
            multiprocessing.current_process().name
        )
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        file_handler = self.FileHandler(
            self.config.FrameworkConfigGetLogPath(process_name),
            mode="w+"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter())

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(ConsoleFormatter())

        # Replace any old handlers
        logger.handlers = [file_handler, stream_handler]

    def disable_console_logging(self, **kwargs):
        """
        + Must be called from inside the process because we should
          remove handler for that root logger
        + Since we add console handler in the last, we can remove
          the last handler to disable console logging
        """
        logger = logging.getLogger()
        logger.removeHandler(logger.handlers[-1])

    def Start(self, options):
        if self.initialise_framework(options):
            return self.run_server()

    def initialise_framework(self, options):
        self.ProxyMode = options["ProxyMode"]
        cprint("Loading framework please wait..")
        # self.initlogger()

        # No processing required, just list available modules.
        if options['ListPlugins']:
            self.PluginHandler.ShowPluginList()
            self.exit_output()
            return False
        self.config.ProcessOptions(options)
        command = self.GetCommand(options['argv'])

        self.StartBotnetMode(options)
        self.StartProxy(options)  # Proxy mode is started in that function.
        self.initialise_plugin_handler_and_params(options)
        # Set anonymised invoking command for error dump info.
        self.error_handler.SetCommand(OutputCleaner.anonymise_command(command))
        return True

    def initialise_plugin_handler_and_params(self, options):
        # The order is important here ;)
        self.PluginHandler = self.get_component("plugin_handler") #plugin_handler.PluginHandler(self, options)
        self.PluginParams = self.get_component("plugin_params")
        self.WorkerManager = worker_manager.WorkerManager()

    def run_server(self):
        """
        This method starts the interface server
        """
        self.FileServer = server.FileServer()
        self.FileServer.start()
        self.InterfaceServer = server.InterfaceServer()
        logging.info(
            "Interface Server started. Visit http://%s:%s",
            self.config.FrameworkConfigGet("UI_SERVER_ADDR"),
            self.config.FrameworkConfigGet("UI_SERVER_PORT"))
        #self.disable_console_logging()
        logging.info("Press Ctrl+C when you spawned a shell ;)")
        self.InterfaceServer.start()

    def ReportErrorsToGithub(self):
        cprint(
            "Do you want to add any extra info to the bug report? "
            "[Just press Enter to skip]")
        info = raw_input("> ")
        cprint(
            "Do you want to add your GitHub username to the report? "
            "[Press Enter to skip]")
        user = raw_input("Reported by @")
        if self.error_handler.AddGithubIssue(Info=info, User=user):
            cprint("Github issue added, Thanks for reporting!!")
        else:
            cprint("Unable to add github issue, but thanks for trying :D")

    def Finish(self, status='Complete', report=True):
        if getattr(self, "TOR_process", None) is not None:
            self.TOR_process.terminate()
        # TODO: Fix this for lions_2014
        # if self.db_config.Get('SIMULATION'):
        #    exit()
        else:
            try:
                self.PluginHandler.CleanUp()
            except AttributeError:  # DB not instantiated yet!
                pass
            finally:
                if getattr(self, "ProxyMode", None) is not None:
                    try:
                        cprint(
                            "Stopping inbound proxy processes and "
                            "cleaning up, Please wait!")
                        self.KillChildProcesses(self.ProxyProcess.pid)
                        self.ProxyProcess.terminate()
                        # No signal is generated during closing process by
                        # terminate()
                        self.TransactionLogger.poison_q.put('done')
                        self.TransactionLogger.join()
                    except:  # It means the proxy was not started.
                        pass
                exit()

    def KillChildProcesses(self, parent_pid, sig=signal.SIGINT):
        ps_command = subprocess.Popen(
            "ps -o pid --ppid %d --noheaders" % parent_pid,
            shell=True,
            stdout=subprocess.PIPE)
        ps_output = ps_command.stdout.read()
        for pid_str in ps_output.split("\n")[:-1]:
            self.KillChildProcesses(int(pid_str), sig)
            try:
                os.kill(int(pid_str), sig)
            except:
                cprint("unable to kill it")

    def decorate_io(self):
        self.FileHandler = catch_io_errors(logging.FileHandler)


def Init(root_dir, owtf_pid, args):
    return Core(root_dir, owtf_pid, args)
