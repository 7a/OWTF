#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2014, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
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

Component to handle data storage and search of all errors
'''

from framework.db import models
from framework.lib import exceptions


class ErrorDB(object):
    def __init__(self, Core):
        self.Core = Core

    def Add(self, Message, Trace):
        error = models.Error(
            owtf_message=Message,
            traceback=Trace)
        self.Core.DB.session.add(error)
        self.Core.DB.session.commit()

    def Delete(self, error_id):
        error = self.Core.DB.session.query(models.Error).get(error_id)
        if error:
            self.Core.DB.session.delete(error)
            self.Core.DB.session.commit()
        else:
            raise exceptions.InvalidErrorReference(
                "No error with id " + str(error_id))

    def GenerateQueryUsingSession(self, criteria):
        query = self.Core.DB.session.query(models.Error)
        if criteria.get('reported', None):
            if isinstance(criteria.get('reported'), list):
                criteria['reported'] = criteria['reported'][0]
            query = query.filter_by(
                reported=self.Core.Config.ConvertStrToBool(
                    criteria['reported']))
        return(query)

    def Update(self, error_id, user_message):
        error = self.Core.DB.session.query(models.Error).get(error_id)
        if not error:  # If invalid error id, bail out
            raise exceptions.InvalidErrorReference(
                "No error with id " + str(error_id))
        error.user_message = patch_data["user_message"]
        self.Core.DB.session.merge(error)
        self.Core.DB.session.commit()

    def DeriveErrorDict(self, error_obj):
        tdict = dict(error_obj.__dict__)
        tdict.pop("_sa_instance_state", None)
        return(tdict)

    def DeriveErrorDicts(self, error_obj_list):
        results = []
        for error_obj in error_obj_list:
            if error_obj:
                results.append(self.DeriveErrorDict(error_obj))
        return results

    def GetAll(self, criteria=None):
        if not criteria:
            criteria = {}
        query = self.GenerateQueryUsingSession(criteria)
        results = query.all()
        return(self.DeriveErrorDicts(results))

    def Get(self, error_id):
        error = self.Core.DB.session.query(models.Error).get(error_id)
        if not error:  # If invalid error id, bail out
            raise exceptions.InvalidErrorReference(
                "No error with id " + str(error_id))
        return(self.DeriveErrorDict(error))
