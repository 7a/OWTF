#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools & facilitate pentesting
Copyright (c) 2013, Abraham Aranguren <name.surname@gmail.com>  http://7-a.org
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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Inbound Proxy Module developed by Bharadwaj Machiraju (blog.tunnelshade.in)
#                     as a part of Google Summer of Code 2013
'''
from multiprocessing import Process, current_process
from framework.http import transaction
from framework.http.proxy.cache_handler import response_from_cache, \
    request_from_cache
from framework.lib.owtf_process import OWTFProcess
from framework import timer
from urlparse import urlparse
import os
import glob
import time
import logging


class TransactionLogger(OWTFProcess):
    """
    This transaction logging process is started seperately from tornado proxy
    This logger checks for *.rd files in cache_dir and saves it as owtf db
    transaction, *.rd files serve as a message that the file corresponding
    to the hash is ready to be converted.
    """
    def derive_target_for_transaction(self, request, response, target_list, host_list):
        for target_id,Target in target_list:
            if request.url.startswith(Target):
                return [target_id, True]
            elif Target in request.url:
                return [target_id, self.get_scope_for_url(request.url, host_list)]
            elif response.headers.get("Referer", None) and response.headers["Referer"].startswith(Target):
                return [target_id, self.get_scope_for_url(request.url, host_list)]
            # This check must be at the last
            elif urlparse(request.url).hostname == urlparse(Target).hostname:
                return [target_id, True]
        return [self.core.DB.Target.GetTargetID(), self.get_scope_for_url(request.url, host_list)]

    def get_scope_for_url(self, url, host_list):
        return((urlparse(url).hostname in host_list))

    def get_owtf_transactions(self, hash_list):
        transactions_dict = None
        target_list = self.core.DB.Target.GetIndexedTargets()
        if target_list: # If there are no targets in db, where are we going to add. OMG
            transactions_dict = {}
            host_list = self.core.DB.Target.GetAllInScope('host_name')

            for request_hash in hash_list:
                request = request_from_cache(request_hash, self.cache_dir)
                response = response_from_cache(request_hash, self.cache_dir)
                target_id, request.in_scope = self.derive_target_for_transaction(request, response, target_list, host_list)
                owtf_transaction = transaction.HTTP_Transaction(timer.Timer())
                owtf_transaction.ImportProxyRequestResponse(request, response)
                try:
                    transactions_dict[target_id].append(owtf_transaction)
                except KeyError:
                    transactions_dict[target_id] = [owtf_transaction]
        return(transactions_dict)

    def get_hash_list(self, cache_dir):
        hash_list = []
        for file_path in glob.glob(os.path.join(cache_dir, "url", "*.rd")):
            request_hash = os.path.basename(file_path)[:-3]
            hash_list.append(request_hash)
            os.remove(file_path)
        return(hash_list)

    def pseudo_run(self):
        try:
            while self.poison_q.empty():
                if glob.glob(os.path.join(self.cache_dir, "url", "*.rd")):
                    hash_list = self.get_hash_list(self.cache_dir)
                    transactions_dict = self.get_owtf_transactions(hash_list)
                    if transactions_dict: # Make sure you donot have None
                        self.core.DB.Transaction.LogTransactionsFromLogger(transactions_dict)
                else:
                    time.sleep(2)
        except KeyboardInterrupt:
            exit()
