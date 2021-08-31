from typing import Any, List, Tuple, Union, Optional, Callable, Type, TypeVar

import base64
import enum
import datetime
import hashlib
import http.server
import random
import requests
import string
import threading
import time
import urllib.parse
import uuid

from socketserver import ThreadingMixIn

import pywim

from pywim import WimObject, WimList

class ApiResult(WimObject):
    def __init__(self):
        self.success = False
        self.message = ''
        self.error = ''
        self.exception = ''

class User(WimObject):
    '''
    User information, such as unique Id, email, and name
    '''
    def __init__(self):
        self.id = ''
        self.email = ''
        self.first_name = ''
        self.last_name = ''
        self.email_verified = False

class Token(WimObject):
    '''
    Authentication token information
    Important! The 'id' attribute contains the token that authenticates the user
    with the server. This must be kept secret and safe.
    '''
    def __init__(self):
        self.id = ''
        self.expires = ''

class UserAuth(WimObject):
    '''
    User authentication response
    '''
    def __init__(self):
        self.user = User()
        self.token = Token()

class Product(WimObject):
    '''
    A product definition in a subscription
    '''

    class UsageType(enum.Enum):
        unlimited = 0
        limited = 1

    def __init__(self, name : str = None):
        self.name = name if name else ''
        self.usage_type = Product.UsageType.limited
        self.used = 0
        self.total = 0

class Subscription(WimObject):
    class Status(enum.Enum):
        unknown = 0
        inactive = 1
        active = 2
        trial = 3

    def __init__(self):
        default_dt = datetime.datetime(1900, 1, 1)

        self.status = Subscription.Status.unknown
        self.start = default_dt
        self.end = default_dt
        self.trial_start = default_dt
        self.trial_end = default_dt
        self.products = WimList(Product)

class JobInfo(WimObject):
    class Type(enum.Enum):
        validation = 101
        optimizaton = 102

    class Status(enum.Enum):
        idle = 101          # Created, but not submitted to a queue
        queued = 102        # Job in queue, but not picked up by an engine yet
        running = 201       # Job is being solved
        finished = 301      # Finished and results are available
        aborted = 401       # Aborted by the user. A run can be aborted before or after it enters the running state
        failed = 402        # The job started, but failed in a graceful fashion. A helpful error message should be available.
        crashed = 403       # The job started, but the process crashed. Helpful error messages are probably not available (e.g. seg fault)

    class Error(WimObject):
        def __init__(self):
            self.message = ''

    def __init__(self):
        default_dt = datetime.datetime(1900, 1, 1)

        self.id = ''
        #self.type = JobInfo.Type.validation
        self.status = JobInfo.Status.idle
        self.progress = 0
        self.queued = default_dt
        self.started = default_dt
        self.finished = default_dt
        self.start_estimate = default_dt
        self.runtime_estimate = 0
        self.runtime_remaining = 0
        self.runtime = 0
        self.result = pywim.smartslice.result.Result()
        self.errors = WimList(JobInfo.Error)


T = TypeVar('T')
U = TypeVar('U')
W = TypeVar('W', bound=WimObject)

ResponseType = Tuple[int, Optional[Union[T, U]]]

class Client:
    def __init__(self, hostname='api.smartslice.xyz', port=443, protocol='https', cluster=None):
        self.hostname = hostname
        self.port = port
        self.protocol = protocol
        self.cluster = cluster
        self._accept_version = '21.0'
        self._bearer_token = None

    @property
    def address(self):
        if self.protocol == 'https' and self.port == 443:
            return '%s://%s' % (self.protocol, self.hostname)
        return '%s://%s:%i' % (self.protocol, self.hostname, self.port)

    def _headers(self):
        '''
        Returns a dictionary of additional headers that will be added
        to every request.
        '''
        hdrs = {
            'Accept-Version': self._accept_version
        }

        if self._bearer_token:
            hdrs['Authorization'] = 'Bearer ' + self._bearer_token

        if self.cluster:
            hdrs['SmartSlice-Cluster'] = self.cluster

        return hdrs

    def _request(self, method : str, endpoint : str, data : Any, **kwargs) -> requests.Response:
        '''
        Assembles an HTTP request and submits it using the requests library.
        '''
        if isinstance(data, bytes):
            request_args = { 'data': data }
        else:
            request_args = { 'json': data }

        if kwargs:
            request_args.update(kwargs)

        request_args['headers'] = self._headers()

        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint

        url = self.address + endpoint

        return requests.request(
            method.lower(),
            url,
            **request_args
        )

    def _get(self, endpoint : str, **kwargs) -> requests.Response:
        return self._request('get', endpoint, None, **kwargs)

    def _post(self, endpoint : str, data : Any = None, **kwargs) -> requests.Response:
        return self._request('post', endpoint, data, **kwargs)

    def _put(self, endpoint : str, data : Any = None, **kwargs) -> requests.Response:
        return self._request('put', endpoint, data, **kwargs)

    def _delete(self, endpoint : str, data : Any = None, **kwargs) -> requests.Response:
        return self._request('delete', endpoint, data, **kwargs)

    @staticmethod
    def _code_and_object(resp : requests.Response, t : Type[W]) -> Tuple[int, W]:
        return resp.status_code, t.from_dict(resp.json())

    def _set_token_from_response(self, resp: requests.Response):
        if resp.status_code in (429, 500):
            return resp.status_code, None

        if resp.status_code == 400:
            return Client._code_and_object(resp, ApiResult)

        if resp.status_code == 200:
            auth = UserAuth.from_dict(resp.json())
            self._bearer_token = auth.token.id
            return resp.status_code, auth

        return Client._code_and_object(resp, ApiResult)

    def get_token(self) -> str:
        return self._bearer_token

    def set_token(self, token_id : str):
        '''
        Set the auth token explicitly. This is useful if the token was stored
        and retrieved locally.
        '''
        self._bearer_token = token_id

    def info(self) -> Tuple[int, Optional[dict]]:
        resp = self._get('/')

        if resp.status_code == 200:
            return resp.status_code, resp.json()

        if resp.status_code == 400:
            return Client._code_and_object(resp, ApiResult)

        return resp.status_code, None

    def basic_auth_login(self, email, password) -> 'ResponseType[UserAuth, ApiResult]':
        resp = self._post(
            '/auth/token',
            {
                'email': email,
                'password': password
            }
        )

        return self._set_token_from_response(resp)

    def oauth_init(self, provider: str, redirect_uri: str, app: Optional[str] = None) -> 'ResponseType[str, ApiResult]':
        endpoint = '/oauth/init?provider={provider}&redirect_uri={redirect_uri}'.format(
            provider=urllib.parse.quote(provider),
            redirect_uri=urllib.parse.quote(redirect_uri)
        )

        if app:
            endpoint += '&app=' + urllib.parse.quote(app)

        resp = self._get(endpoint, allow_redirects=False)

        if resp.status_code == 400:
            return Client._code_and_object(resp, ApiResult)

        if resp.is_redirect:
            return resp.status_code, resp.headers.get('Location')

        result = ApiResult()
        result.error = 'Unexpected status code'

        return resp.status_code, result

    def oauth_token(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str
    ) -> 'ResponseType[UserAuth, ApiResult]':
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier
        }

        resp = self._post('/oauth/token', data=token_request_data)

        return self._set_token_from_response(resp)

    def whoami(self) -> 'ResponseType[UserAuth, ApiResult]':
        resp = self._get('/auth/whoami')

        if resp.status_code in (401, 500):
            return resp.status_code, None

        if resp.status_code == 400:
            return Client._code_and_object(resp, ApiResult)

        if resp.status_code == 200:
            return Client._code_and_object(resp, UserAuth)

        return Client._code_and_object(resp, ApiResult)

    def refresh_token(self) -> 'ResponseType[UserAuth, ApiResult]':
        resp = self._put('/auth/token')

        if resp.status_code in (401, 500):
            return resp.status_code, None

        if resp.status_code == 400:
            return Client._code_and_object(resp, ApiResult)

        if resp.status_code == 200:
            # The token id will be the same, so we don't need to update it
            return Client._code_and_object(resp, UserAuth)

        return Client._code_and_object(resp, ApiResult)

    def release_token(self) -> Tuple[int, Optional[ApiResult]]:
        resp = self._delete('/auth/token')

        if resp.status_code in (401, 500):
            return resp.status_code, None

        if resp.status_code == 400:
            return Client._code_and_object(resp, ApiResult)

        self._bearer_token = None

        return Client._code_and_object(resp, ApiResult)

    def new_smartslice_job(self, tmf : bytes) -> 'ResponseType[JobInfo, ApiResult]':
        '''
        Submits the provided 3MF as a new job and returns the new JobInfo object.
        '''
        resp = self._post('/smartslice', tmf)

        if resp.status_code in (401, 500):
            return resp.status_code, None

        if resp.status_code == 400:
            return Client._code_and_object(resp, ApiResult)

        return Client._code_and_object(resp, JobInfo)

    def smartslice_job(self, job_id : str, include_results : bool = False) -> 'ResponseType[JobInfo, ApiResult]':
        '''
        Retrieves a JobInfo object from an existing job id. Will return a 404
        if the user doesn't have access to the specified job.
        '''
        if include_results:
            resp = self._get('/smartslice/result/%s' % job_id)
        else:
            resp = self._get('/smartslice/%s' % job_id)

        if resp.status_code in (401, 404, 429, 500):
            return resp.status_code, None

        if resp.status_code == 400:
            return Client._code_and_object(resp, ApiResult)

        return Client._code_and_object(resp, JobInfo)

    def smartslice_job_abort(self, job_id : str) -> Tuple[int, Optional[JobInfo]]:
        '''
        Requests the job with the given id should be aborted. This will return
        the updated JobInfo object to reflect the new status after the server
        processes the abort request.
        '''
        resp = self._delete('/smartslice/%s' % job_id)

        if resp.status_code == 400:
            return Client._code_and_object(resp, ApiResult)

        if resp.status_code == 200:
            return Client._code_and_object(resp, JobInfo)

        return resp.status_code, None

    def smartslice_job_wait(
        self,
        job_id : str,
        timeout : int = 600,
        callback : Callable[[JobInfo], bool] = None
    ) -> 'ResponseType[JobInfo, ApiResult]':
        '''
        This is a blocking function that will periodically poll the job status until
        it completes. Additionally, a timeout parameter can be given to specify the maximum
        amount of time, in seconds, to poll for. A callback function can be provided
        that will be called periodically with the JobInfo object so the caller can take
        actions as the job progresses. The callback must return a bool specifying if the
        job should be aborted (True) or not (False).
        '''

        start_period = 1
        max_poll_period = 30
        poll_multiplier = 1.5

        fperiod = lambda previous_period: min(max_poll_period, previous_period * poll_multiplier)

        period = start_period
        start_poll = time.time()

        while True:
            time.sleep(period)
            period = fperiod(period)

            status_code, job = self.smartslice_job(job_id, include_results=True)

            if status_code == 429:
                # We hit a rate limit, so check again after the poll period
                continue

            if status_code != 200:
                return status_code, job

            assert isinstance(job, JobInfo)

            if job.status in (
                JobInfo.Status.finished,
                JobInfo.Status.failed,
                JobInfo.Status.aborted,
                JobInfo.Status.crashed
            ):
                break

            if timeout is not None and (time.time() - start_poll) > timeout:
                break

            if callback:
                abort = callback(job)
                if abort:
                    return self.smartslice_job_abort(job.id)

        return status_code, job

    def smartslice_subscription(self) -> 'ResponseType[Subscription, ApiResult]':
        '''
        Retrieve the user's subscription. If the user does not have
        a subscription a Subscription object with no Products will
        be returned.
        '''
        resp = self._get('/smartslice/subscription')

        if resp.status_code in (401, 429, 500):
            return resp.status_code, None

        return Client._code_and_object(resp, Subscription)


class _ThreadingHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    pass


class OAuth2Handler:
    DEFAULT_PORTS = (47001, 47002, 47003)

    class State(enum.Enum):
        UrlOpenFail = 1
        CodeInputRequired = 2
        Listening = 3
        PageNotOpened = 4

    def __init__(self,
        client: Client,
        callback: Callable[[int, Union[UserAuth, ApiResult]], None],
        url_opener: Optional[Callable[[str], bool]] = None,
        ports: Optional[List[int]] = None,
        client_id: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        login_form_basic: bool = True,
        login_form_providers: Optional[List[str]] = None
    ) -> None:
        self._client = client
        self._callback = callback
        self._ports = ports if ports else OAuth2Handler.DEFAULT_PORTS
        self._client_id = client_id
        self._scopes = scopes or ['account.read']
        self._login_form_basic = login_form_basic
        self._login_form_providers = login_form_providers or []

        # Redirect and server details will be set in start
        self._redirect_uri = None
        self._code_verifier = None
        self._server = None
        self._state = str(uuid.uuid4())

        if url_opener:
            self._url_opener = url_opener
        else:
            import webbrowser
            self._url_opener = webbrowser.open

    def _listen_attempt(self, port: int):
        redirect_handler_class = _make_local_redirect_handler_class(self)

        try:
            if hasattr(http.server, 'ThreadingHTTPServer'):
                self._server = http.server.ThreadingHTTPServer(('localhost', port), redirect_handler_class)
            else:
                self._server = _ThreadingHTTPServer(('localhost', port), redirect_handler_class)

            thread = threading.Thread(target=self._server.serve_forever, name='SmartSliceOAuthHttpCallback')
            thread.start()
        except:
            return False

        return True

    @staticmethod
    def _make_code_challenge(length: int = 32) -> str:
        chars = string.ascii_letters + string.digits

        code = ''.join([ random.choice(chars) for i in range(length) ])

        code_hash = hashlib.sha256()
        code_hash.update(code.encode())

        challenge = base64.urlsafe_b64encode(code_hash.digest())

        return code, challenge.decode().strip('=')

    def start(self, register: bool = False, provider: Optional[str] = None, open_page: bool = True) -> Tuple[State, Optional[str]]:
        # Attempt to open a local http server to listen for the callback
        listening = False

        for p in self._ports:
            redirect_uri = 'http://localhost:%i' % p

            listening = self._listen_attempt(p)

            if listening:
                break

        # If we can't start a local http server then we'll fallback to
        # using a callback on the thor API that will show the code with instructions
        if listening:
            success_state = OAuth2Handler.State.Listening
        else:
            if open_page:
                success_state = OAuth2Handler.State.CodeInputRequired
            else:
                return (OAuth2Handler.State.PageNotOpened, None)

            redirect_uri = self._client.address + '/oauth/code'

        self._redirect_uri = redirect_uri

        self._code_verifier, code_challenge = self._make_code_challenge()

        query_params = {
            'client_id': self._client_id,
            'redirect_uri': self._redirect_uri,
            'scope': ','.join(self._scopes),
            'response_type': 'code',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'state': self._state,
            'basic': self._login_form_basic
        }

        if self._login_form_providers:
            query_params['providers'] = ','.join(self._login_form_providers)

        if register:
            query_params['register'] = register

        oauth_auth_url = self.thor_address() + \
            '/oauth/authorize?' + urllib.parse.urlencode(query_params)

        if not self._url_opener(oauth_auth_url):
            return (OAuth2Handler.State.UrlOpenFail, 'Failed to open authorize URL in browser')

        return (success_state, None)

    def stop(self):
        if self._server:
            server = self._server
            self._server = None
            server.shutdown()

    def redirect_called(self, code: str, state: str) -> Optional[str]:
        status, resp = self._client.oauth_token(
            code, self._client_id, self._redirect_uri, self._code_verifier
        )

        error = None

        if self._callback:
            self._callback(status, resp)

        if status == 400:
            error = resp.error
        elif status != 200:
            error = 'Unexpected status on SmartSlice OAuth login: %i' % status

        return error

    def redirect_called_error(self, error: str):
        result = ApiResult()
        result.success = False
        result.error = error

        if self._callback:
            self._callback(None, result)

    def redirect_complete(self) -> None:
        self.stop()

    def thor_address(self) -> str:
        return self._client.address

    def state(self) -> str:
        return self._state

def _make_local_redirect_handler_class(handler: OAuth2Handler) -> Callable[[], http.server.BaseHTTPRequestHandler]:
    class _OAuthLocalRedirectHandler(http.server.BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs) -> None:
            self.handler = handler

            super().__init__(*args, **kwargs)

        def do_HEAD(self) -> None:
            self.do_GET()

        def do_GET(self) -> None:
            parsed_url = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed_url.query)

            code = query.get('code', [None])[0]
            state = query.get('state', [None])[0]
            error = query.get('error', [None])[0]

            if not error:
                if not code:
                    error = '"code" was missing from redirect URL'

                if not state:
                    error = '"state" was missing from redirect URL'

                if state != self.handler.state():
                    error = '"state" does not match the provided state value'

            if error:
                # If we have an error here then there's no reason to even try to
                # retrieve a token, so we call the appropriate callbacks and return
                self.handler.redirect_called_error(error)
                self._error(error)
            else:
                error = self.handler.redirect_called(code, state)

                if error:
                    self._error(error)
                else:
                    self._success('Logged in!')

            self.handler.redirect_complete()

        def _redirect(self, endpoint):
            address = '%s/%s' % (self.handler.thor_address(), endpoint.lstrip('/'))

            self.send_response(302)
            self.send_header('Location', address)
            self.end_headers()

            self.wfile.write(('Redirecting to %s' % address).encode())

        def _error(self, error: str) -> None:
            self._redirect(
                '/oauth/complete?error={error}'.format(
                    error=urllib.parse.quote(error)
                )
            )

        def _success(self, message: str) -> None:
            self._redirect(
                '/oauth/complete?message={message}'.format(
                    message=urllib.parse.quote(message)
                )
            )

    return _OAuthLocalRedirectHandler
