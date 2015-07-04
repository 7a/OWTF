import tornado.web
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
import json
from framework.lib import exceptions
from framework.lib.general import cprint
from framework.interface import custom_handlers


class PluginDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    #TODO: Creation of user plugins

    def get(self, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # Check if plugin_group is present in url
                self.write(self.application.Core.DB.Plugin.GetAll(filter_data))
            if plugin_group and (not plugin_type) and (not plugin_code):
                filter_data.update({"group": plugin_group})
                self.write(self.application.Core.DB.Plugin.GetAll(filter_data))
            if plugin_group and plugin_type and (not plugin_code):
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type": plugin_type, "group": plugin_group})
                self.write(self.application.Core.DB.Plugin.GetAll(filter_data))
            if plugin_group and plugin_type and plugin_code:
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type": plugin_type, "group": plugin_group, "code": plugin_code})
                results = self.application.Core.DB.Plugin.GetAll(filter_data)  # This combination will be unique, so have to return a dict
                if results:
                    self.write(results[0])
                else:
                    raise tornado.web.HTTPError(400)
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class TargetConfigHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, target_id=None):
        try:
            # If no target_id, means /target is accessed with or without filters
            if not target_id:
                # Get all filter data here, so that it can be passed
                filter_data = dict(self.request.arguments)
                self.write(self.application.Core.DB.Target.GetTargetConfigs(filter_data))
            else:
                self.write(self.application.Core.DB.Target.GetTargetConfigForID(target_id))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_id=None):
        if (target_id) or (not self.get_argument("target_url", default=None)):  # How can one post using an id xD
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.Target.AddTargets(
                dict(self.request.arguments)["target_url"])
            self.set_status(201)  # Stands for "201 Created"
        except exceptions.DBIntegrityException as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(409)
        except exceptions.UnresolvableTargetException as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(409)

    def put(self, target_id=None):
        return self.patch(target_id)

    def patch(self, target_id=None):
        if not target_id or not self.request.arguments:
            raise tornado.web.HTTPError(400)
        try:
            patch_data = dict(self.request.arguments)
            self.application.Core.DB.Target.UpdateTarget(patch_data, ID=target_id)
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.Target.DeleteTarget(ID=target_id)
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class TargetConfigSearchHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.write(self.application.Core.DB.Target.SearchTargetConfigs(
                filter_data=filter_data))
        except exceptions.InvalidParameterType as e:
            raise tornado.web.HTTPError(400)


class OWTFSessionHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, session_id=None, action=None):
        if action is not None:  # Action must be there only for put
            raise tornado.web.HTTPError(400)
        if session_id is None:
            filter_data = dict(self.request.arguments)
            self.write(self.application.Core.DB.OWTFSession.get_all(filter_data))
        else:
            try:
                self.write(self.application.Core.DB.OWTFSession.get(session_id))
            except exceptions.InvalidSessionReference:
                raise tornado.web.HTTPError(400)

    def post(self, session_id=None, action=None):
        if session_id is not None or \
           self.get_argument("name", None) is None or \
           action is not None:
            # Not supposed to post on specific session
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.OWTFSession.add_session(
                self.get_argument("name"))
            self.set_status(201)  # Stands for "201 Created"
        except exceptions.DBIntegrityException:
            raise tornado.web.HTTPError(409)

    def patch(self, session_id=None, action=None):
        target_id = self.get_argument("target_id", None)
        if session_id is None or \
           (target_id is None and action in ["add", "remove"]):
            raise tornado.web.HTTPError(400)
        try:
            if action == "add":
                self.application.Core.DB.OWTFSession.add_target_to_session(
                    int(self.get_argument("target_id")),
                    session_id=int(session_id))
            elif action == "remove":
                self.application.Core.DB.OWTFSession.remove_target_from_session(
                    int(self.get_argument("target_id")),
                    session_id=int(session_id))
            elif action == "activate":
                self.application.Core.DB.OWTFSession.set_session(
                    int(session_id))
        except exceptions.InvalidTargetReference:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidSessionReference:
            raise tornado.web.HTTPError(400)

    def delete(self, session_id=None, action=None):
        if session_id is None or \
           action is not None:
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.OWTFSession.delete_session(
                int(session_id))
        except exceptions.InvalidSessionReference:
            raise tornado.web.HTTPError(400)


class SessionsDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        try:
            # gets the session_data for the target
            self.write(self.application.Core.DB.Transaction.GetSessionData(target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidTransactionReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    def put(self):
        raise tornado.web.HTTPError(405)

    def patch(self):
        raise tornado.web.HTTPError(405)


class ZestScriptHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST']

    def get(self, target_id=None, transaction_id=None):  # get handles zest consoles functions
        if not target_id:  # does not make sense if no target id provided
            raise tornado.web.HTTPError(400)
        try:
            args = self.request.arguments
            if(not any(args)):  # check if arguments is empty then load zest console
                target_scripts, record_scripts = self.application.Core.zest.GetAllScripts(target_id)
                tdict = {}
                tdict["target_scripts"] = target_scripts
                tdict["recorded_scripts"] = record_scripts
                self.write(tdict)
            elif 'script' in args and 'record' in args and 'run' not in args:  # get zest script content
                if args['record'][0] == "true":  # record script
                    content = self.application.Core.zest.GetRecordScriptContent(args['script'][0])
                else:  # target script
                    content = self.application.Core.zest.GetTargetScriptContent(target_id, args['script'][0])
                self.write({"content": content})
            elif 'script' in args and 'record'in args and 'run' in args:  # runner handling
                if args['run'][0] == "true":
                    if args['record'][0] == "true":  # run record script
                        result = self.application.Core.zest.RunRecordScript(args['script'][0])
                    else:  # run target script
                        result = self.application.Core.zest.RunTargetScript(target_id, args['script'][0])
                    self.write({"result": result})
            else:
                if 'script' not in args and 'record' in args:  # Recorder handling
                    if args['record'][0] == "true" and 'file' in args:
                        if not self.application.Core.zest.StartRecorder(args['file'][0]):
                            self.write({"exists": "true"})
                    else:
                        self.application.Core.zest.StopRecorder()
        except exceptions.InvalidTargetReference as e:
                cprint(e.parameter)
                raise tornado.web.HTTPError(400)

# all script creation requests are post methods, Zest class instance then handles the script creation part

    def post(self, target_id=None, transaction_id=None):  # handles actual zest script creation
            if not target_id:  # does not make sense if no target id provided
                raise tornado.web.HTTPError(400)
            try:
                if transaction_id:
                    Scr_Name = self.get_argument('name', '')
                    if not self.application.Core.zest.TargetScriptFromSingleTransaction(transaction_id, Scr_Name, target_id): #zest script creation from single transaction
                        self.write({"exists": "true"})
                else:  # multiple transactions
                    trans_list = self.get_argument('trans', '')   # get transaction ids
                    Scr_Name = self.get_argument('name', '')  # get script name
                    transactions = json.loads(trans_list)  # convert to string from json
                    if not self.application.Core.zest.TargetScriptFromMultipleTransactions(target_id, Scr_Name, transactions): #zest script creation from multiple transactions
                        self.write({"exists": "true"})
            except exceptions.InvalidTargetReference as e:
                cprint(e.parameter)
                raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        raise tornado.web.HTTPError(405)


class ReplayRequestHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = {'POST'}

    @tornado.web.asynchronous
    def get(self, target_id=None, transaction_id=None):
        raise tornado.web.HTTPError(405)

    def post(self, target_id=None, transaction_id=None):
        rw_request = self.get_argument("get_req", '')  # get particular request
        parsed_req = HTTPRequest(rw_request)  # parse if its a valid HTTP request
        if(parsed_req.error_code == None):
            replay_headers = self.RemoveIfNoneMatch(parsed_req.headers)
            self.application.Core.Requester.SetHeaders(replay_headers)  #Set the headers
            trans_obj = self.application.Core.Requester.Request(parsed_req.path, parsed_req.command)  # make the actual request using requester module
            res_data = {}  # received response body and headers will be saved here
            res_data['STATUS'] = trans_obj.Status
            res_data['HEADERS'] = str(trans_obj.ResponseHeaders)
            res_data['BODY'] = trans_obj.DecodedContent
            self.write(res_data)
        else:
            print "Cannot send the given HTTP Request"
            #send something back to interface to let the user know

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        raise tornado.web.HTTPError(405)  # @UndefinedVariable

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        raise tornado.web.HTTPError(405)  # @UndefinedVariable

    def RemoveIfNoneMatch(self, headers):  # Required to force request and not respond with the cached response
        del headers["If-None-Match"]
        return headers


class HTTPRequest(BaseHTTPRequestHandler):
    # this class parses the raw request and  verifies
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

"""
    Remove this at the end
    def print_all(self):
        print self.error_code       # None  (check this first)
        print self.command          # "GET"
        print self.path             # "/who/ken/trust.html"
        print self.request_version  # "HTTP/1.1"
        print len(self.headers)     # 3
        print self.headers   # ['accept-charset', 'host', 'accept']
        print self.headers['host']
"""


class ForwardToZAPHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None, transaction_id=None):
        try:
            if not transaction_id or not target_id:
                raise tornado.web.HTTPError(400)
            else:
                self.application.Core.zap_api_handler.ForwardRequest(target_id, transaction_id)
        except exceptions.InvalidTargetReference as e:
                cprint(e.parameter)
                raise tornado.web.HTTPError(400)


class TransactionDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'DELETE']

    def get(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                self.write(
                    self.application.Core.DB.Transaction.GetByIDAsDict(
                        int(transaction_id),
                        target_id=int(target_id)))
            else:
                # Empty criteria ensure all transactions
                filter_data = dict(self.request.arguments)
                self.write(
                    self.application.Core.DB.Transaction.GetAllAsDicts(
                        filter_data,
                        target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidTransactionReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    def put(self):
        raise tornado.web.HTTPError(405)

    def patch(self):
        raise tornado.web.HTTPError(405)

    def delete(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                self.application.Core.DB.Transaction.DeleteTransaction(
                    int(transaction_id),
                    target_id=int(target_id))
            else:
                raise tornado.web.HTTPError(400)
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class TransactionSearchHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        if not target_id:  # Must be a integer target id
            raise tornado.web.HTTPError(400)
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.write(self.application.Core.DB.Transaction.SearchAll(
                filter_data,
                target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidTransactionReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class URLDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            self.write(self.application.Core.DB.URL.GetAll(filter_data, target_id=target_id))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        #TODO: allow modification of urls from the ui, may be adjusting scope etc.. but i don't understand it's use yet ;)
        raise tornado.web.HTTPError(405)  # @UndefinedVariable

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        #TODO: allow deleting of urls from the ui
        raise tornado.web.HTTPError(405)  # @UndefinedVariable


class URLSearchHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        if not target_id:  # Must be a integer target id
            raise tornado.web.HTTPError(400)
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.write(self.application.Core.DB.URL.SearchAll(
                filter_data,
                target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class PluginOutputHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group: # First check if plugin_group is present in url
                self.write(self.application.Core.DB.POutput.GetAll(filter_data, target_id=target_id))
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
                self.write(self.application.Core.DB.POutput.GetAll(filter_data, target_id=target_id))
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
                self.write(self.application.Core.DB.POutput.GetAll(filter_data, target_id=target_id))
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group, "plugin_code": plugin_code})
                results = self.application.Core.DB.POutput.GetAll(filter_data, target_id=target_id)
                if results:
                    self.write(results[0])
                else:
                    raise tornado.web.HTTPError(400)
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    def put(self):
        raise tornado.web.HTTPError(405)

    def patch(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            if (not target_id) or (not plugin_group) or (not plugin_type) or (not plugin_code):
                raise tornado.web.HTTPError(400)
            else:
                patch_data = dict(self.request.arguments)
                self.application.Core.DB.POutput.Update(plugin_group, plugin_type, plugin_code, patch_data, target_id=int(target_id))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group: # First check if plugin_group is present in url
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id=int(target_id))
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id=int(target_id))
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id=int(target_id))
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group, "plugin_code": plugin_code})
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id=int(target_id))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class WorkerHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE']

    def get(self, worker_id=None, action=None):
        if not worker_id:
            self.write(self.application.Core.WorkerManager.get_worker_details())
        try:
            if worker_id and (not action):
                self.write(self.application.Core.WorkerManager.get_worker_details(int(worker_id)))
            if worker_id and action:
                getattr(self.application.Core.WorkerManager, action + '_worker')(int(worker_id))
        except exceptions.InvalidWorkerReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, worker_id=None, action=None):
        if worker_id or action:
            raise tornado.web.HTTPError(400)
        self.application.Core.WorkerManager.create_worker()
        self.set_status(201)  # Stands for "201 Created"

    def delete(self, worker_id=None, action=None):
        if (not worker_id) or action:
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.WorkerManager.delete_worker(int(worker_id))
        except exceptions.InvalidWorkerReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class WorklistHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE', 'PATCH']

    def get(self, work_id=None, action=None):
        try:
            if work_id is None:
                criteria = dict(self.request.arguments)
                self.write(self.application.Core.DB.Worklist.get_all(criteria))
            else:
                self.write(self.application.Core.DB.Worklist.get(int(work_id)))
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidWorkReference:
            raise tornado.web.HTTPError(400)

    def post(self, work_id=None, action=None):
        if work_id is not None or action is not None:
            tornado.web.HTTPError(400)
        try:
            filter_data = dict(self.request.arguments)
            if not filter_data:
                raise tornado.web.HTTPError(400)
            plugin_list = self.application.Core.DB.Plugin.GetAll(filter_data)
            target_list = self.application.Core.DB.Target.GetTargetConfigs(filter_data)
            if (not plugin_list) or (not target_list):
                raise tornado.web.HTTPError(400)
            self.application.Core.DB.Worklist.add_work(
                target_list,
                plugin_list,
                force_overwrite=self.application.Core.Config.ConvertStrToBool(
                    self.get_argument("force_overwrite", "False"))
            )
            self.set_status(201)
        except exceptions.InvalidTargetReference as e:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            raise tornado.web.HTTPError(400)

    def delete(self, work_id=None, action=None):
        if work_id is None or action is not None:
            tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.Worklist.remove_work(int(work_id))
            self.set_status(200)
        except exceptions.InvalidTargetReference as e:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidWorkReference as e:
            raise tornado.web.HTTPError(400)

    def patch(self, work_id=None, action=None):
        if work_id is None or action is None:
            tornado.web.HTTPError(400)
        try:
            work_id = int(work_id)
            if work_id != 0:  # 0 is like broadcast address
                if action == 'resume':
                    self.application.Core.DB.Worklist.patch_work(
                        work_id, active=True)
                elif action == 'pause':
                    self.application.Core.DB.Worklist.patch_work(
                        work_id, active=False)
            else:
                if action == 'pause':
                    self.application.Core.DB.Worklist.pause_all()
                elif action == 'resume':
                    self.application.Core.DB.Worklist.resume_all()
        except exceptions.InvalidWorkReference as e:
            raise tornado.web.HTTPError(400)


class WorklistSearchHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            criteria = dict(self.request.arguments)
            criteria["search"] = True
            self.write(self.application.Core.DB.Worklist.search_all(criteria))
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)


class ConfigurationHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ('GET', 'PATCH')

    def get(self):
        filter_data = dict(self.request.arguments)
        self.write(self.application.Core.DB.Config.GetAll(filter_data))

    def patch(self):
        for key, value_list in self.request.arguments.items():
            try:
                self.application.Core.DB.Config.Update(key, value_list[0])
            except exceptions.InvalidConfigurationReference:
                raise tornado.web.HTTPError(400)


class ErrorDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ('GET', 'PATCH', 'DELETE')

    def get(self, error_id=None):
        if error_id is None:
            filter_data = dict(self.request.arguments)
            self.write(self.application.Core.DB.Error.GetAll(filter_data))
        else:
            try:
                self.write(self.application.Core.DB.Error.Get(error_id))
            except exceptions.InvalidErrorReference:
                raise tornado.web.HTTPError(400)

    def patch(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        if self.request.arguments.get_argument("user_message", default=None):
            raise tornado.web.HTTPError(400)
        self.application.Core.DB.Error.Update(
            error_id,
            self.request.arguments.get_argument("user_message"))

    def delete(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.Error.Delete(error_id)
        except exceptions.InvalidErrorReference:
            raise tornado.web.HTTPError(400)


class PlugnhackHandler(custom_handlers.APIRequestHandler):
    """
    API handler for Plug-n-Hack. Purpose of this handler is to catch
    parameters defining actions (or/and) state that were sent from Plug-n-Hack
    commands invoked in browser, validate them, then send to proxy Plug-n-Hack
    Handler that will process received information and take action corresponding to received information (i.e inject probe into a target, start/stop monitor a target)
    """
    SUPPORTED_METHODS = ['POST']
    # PnH API Handler must accept and send only an action that is a member of VALID_ACTIONS group
    VALID_ACTIONS = ["probe","monitor","oracle","startMonitoring","stopMonitoring"]

    def post(self):
        # Extract useful information from POST request and store it as a dictionary data structure
        self.message = dict(self.request.arguments)
        # Extract value of url, action and state request parameters from request body
        # Request parameters values by default is []
        self.url = self.get_body_argument("url", default=[])
        self.action = self.get_body_argument("action", default=[])
        self.state = self.get_body_argument("state", default=[])

        # Validate url parameter
        try:
            if not self.url:
                pass
            elif self.application.Core.DB.URL.IsURL(self.url):
                pass
            else:
                raise exceptions.InvalidUrlReference(400)
        except exceptions.InvalidUrlReference:
            raise tornado.web.HTTPError(400, "exceptions.Invalid URL")
        # Validate action parameter
        try:
            if (self.action in self.VALID_ACTIONS) or (not self.action):
                pass
            else:
                raise exceptions.InvalidActionReference(400)
        except exceptions.InvalidActionReference:
            raise tornado.web.HTTPError(400, "exceptions.Invalid action")
        # Validate state parameter
        try:
            if (self.state == "on") or (self.state == "off") or (not self.state):
                pass
            else:
                raise exceptions.InvalidActionReference(400)
        except exceptions.InvalidActionReference:
            raise tornado.web.HTTPError(400, "exceptions.Invalid action state")
        # If received message is valid, send it to proxy PnH Handler and log this event
        try:
            if not self.message:
                raise exceptions.InvalidMessageReference
            else:
                # TO DO: send message to proxy handler and verify if event registered in log file
                self.application.Core.write_event(json.dumps(self.message), 'a')
        except exceptions.InvalidMessageReference:
            raise tornado.web.HTTPError(412, "Empty message")
        except IOError as e:
            cprint("\n")
            cprint("I/O error at event writing: ({0}): {1}".format(e.errno, e.strerror))
            cprint("\n")
