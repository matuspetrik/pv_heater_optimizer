import json
import requests
from pprint import pprint
import sys
import time
from Lib import Logger as logger
import Lib.DataControl as dtctl


class VictronApi:

    def __init__(self, vars):
        self.vars = vars
        self.username = self.vars.username
        self.password = self.vars.password
        self.logInUrl = self.vars.logInUrl
        self.logOutUrl = self.vars.logOutUrl
        self.diagsUrl = self.vars.diagsUrl
        self.loginDict = {'username':f'{self.username}','password':f'{self.password}'}
        self.loginString = json.dumps(self.loginDict)
        self.timeout = 5
        self.token = None

    def getToken(self):
        currentMethodName = sys._getframe(  ).f_code.co_name
        self.curFn = f'{__name__}.{currentMethodName}'
        try:
            response = requests.post(self.logInUrl, self.loginString, timeout=self.timeout)
            # response.raise_for_status()
            self.token = json.loads(response.text)["token"]
        except Exception as inst:
            msg = f'\tFn: { self.curFn }:: E: {inst}:: '
            logger.file(msg)
        else:
            self.headers = {"X-Authorization": "Bearer " + self.token}
            self.headers["Content-Type"] = "application/json"
            ok = 'OK' if response.ok else 'NOK'
            msg = f'\t{ self.curFn }; { response.status_code }: { ok }.'
            logger.file(msg)

    def __del__(self):
        currentMethodName = sys._getframe(  ).f_code.co_name
        curFn = f'{__name__}.{currentMethodName}'
        try:
            response = requests.get(self.logOutUrl, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
        except Exception as inst:
            msg = f'\tFn: {curFn}:: E: {inst}:: '
            logger.file(msg)
        else:
            ok = 'OK' if response.ok else 'NOK'
            msg = f'\t{curFn}; {response.status_code}: {ok}.'
            logger.file(msg)

    def getdata(self):
        currentMethodName = sys._getframe(  ).f_code.co_name
        curFn = f'{ __name__ }.{ currentMethodName }'
        _res = None
        _cnt = 0
        while _res is None and _cnt < 5:
            _res = True
            _cnt += 1
            try:
                response = requests.get(self.diagsUrl, headers=self.headers, timeout=self.timeout)
                # response.raise_for_status()
                if response.status_code in [401, 403]:
                    raise ConnectionRefusedError(f"\tToken has timed out. Status code: { response.status_code }.")
                if response.status_code != 200:
                    raise ConnectionError(f"\tForecast connection status is { response.status_code }.")
            except ConnectionRefusedError as inst:
                _res = None
                msg = f'\tFn: { curFn }:: E: { repr(inst) }:: '
                logger.file(msg)
                time.sleep(self.timeout)
                self.getToken()
            except Exception as inst:
                _res = None
                msg = f'\tFn: { curFn }:: E: { repr(inst) }:: '
                logger.file(msg)
                time.sleep(self.timeout)
            else:
                ok = 'OK' if response.ok else 'NOK'
                msg = f'\t{ curFn }; { response.status_code }: { ok }.'
                logger.file(msg)
                return response.json()["records"]
        return False

class getPortalData:

    def __init__(self, vars):
        _res = None
        while _res is None:
            _res = True
            try:
                self.vicApi = VictronApi(vars)
                self.vicApi.getToken()
            except Exception as inst:
                _res = None
                logger.file(f"{ inst }")
                time.sleep(5)

    def getData(self):
        return self.vicApi.getdata()
