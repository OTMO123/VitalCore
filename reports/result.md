/usr/local/lib/python3.11/site-packages/httpx/_models.py:199: in update
    headers = Headers(headers)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <[AttributeError("'Headers' object has no attribute '_encoding'") raised in repr()] Headers object at 0x7caa7b20bc50>
headers = <coroutine object TestProtectedEndpoints.auth_headers at 0x7caa81046740>        
encoding = None

    def __init__(
        self,
        headers: typing.Optional[HeaderTypes] = None,
        encoding: typing.Optional[str] = None,
    ) -> None:
        if headers is None:
            self._list = []  # type: typing.List[typing.Tuple[bytes, bytes, bytes]]       
        elif isinstance(headers, Headers):
            self._list = list(headers._list)
        elif isinstance(headers, Mapping):
            self._list = [
                (
                    normalize_header_key(k, lower=False, encoding=encoding),
                    normalize_header_key(k, lower=True, encoding=encoding),
                    normalize_header_value(v, encoding),
                )
                for k, v in headers.items()
            ]
        else:
>           self._list = [
                (
                    normalize_header_key(k, lower=False, encoding=encoding),
                    normalize_header_key(k, lower=True, encoding=encoding),
                    normalize_header_value(v, encoding),
                )
                for k, v in headers
            ]
E           TypeError: 'coroutine' object is not iterable

/usr/local/lib/python3.11/site-packages/httpx/_models.py:79: TypeError

 app/tests/smoke/test_core_endpoints.py::TestProtectedEndpoints.test_iris_api_endpoints ⨯55% █████▌    

―――――――――――――――――― TestEndpointSecurity.test_all_endpoints_require_auth ――――――――――――――――――

self = <app.tests.smoke.test_core_endpoints.TestEndpointSecurity object at 0x7caa81ab2bd0>
async_test_client = <httpx.AsyncClient object at 0x7caa7b776f90>

    @pytest.mark.asyncio
    async def test_all_endpoints_require_auth(self, async_test_client):
        """
        Verify all sensitive endpoints require authentication.
        Critical for PHI protection.
        """
        # Endpoints that should require auth
        protected_endpoints = [
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/auth/users", "GET"),
            ("/api/v1/audit-logs", "GET"),
            ("/api/v1/iris/status", "GET"),
            ("/api/v1/iris/sync", "POST"),
        ]

        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = await async_test_client.get(endpoint)
            elif method == "POST":
                response = await async_test_client.post(endpoint, json={})

>           assert response.status_code == 401, f"{endpoint} not protected!"
E           AssertionError: /api/v1/auth/me not protected!
E           assert 403 == 401
E            +  where 403 = <Response [403 Forbidden]>.status_code

app/tests/smoke/test_core_endpoints.py:193: AssertionError
---------------------------------- Captured stdout call ----------------------------------
2025-07-31 00:49:05 [info     ] CSP configured for development mode allowed_localhost=True unsafe_eval=True
2025-07-31 00:49:05 [debug    ] Security headers relaxed for development mode
2025-07-31 00:49:05 [info     ] Security headers applied       client_ip=127.0.0.1 csp_nonce=V0bVMUoQ... headers_applied=['Content-Security-Policy', 'X-Content-Type-Options', 'Referrer-Policy', 'Permissions-Policy', 'Cross-Origin-Embedder-Policy', 'Cross-Origin-Opener-Policy', 'Cross-Origin-Resource-Policy', 'X-Frame-Options', 'X-XSS-Protection', 'X-Permitted-Cross-Domain-Policies', 'Cache-Control', 'Pragma', 'Expires', 'X-Healthcare-Data', 'X-PHI-Protection', 'Report-To'] method=GET path=/api/v1/auth/me

 app/tests/smoke/test_core_endpoints.py::TestEndpointSecurity.test_all_endpoints_require_auth ⨯56% █████▋    
 app/tests/smoke/test_core_endpoints.py::TestEndpointSecurity.test_cors_headers ✓58% █████▊                                                                                         
 app/tests/smoke/test_core_endpoints.py::TestEndpointSecurity.test_response_headers_security ✓60% ██████    

―――――――――――――――――― TestEndpointPerformance.test_endpoint_response_times ――――――――――――――――――

self = MemoryObjectReceiveStream(_state=MemoryObjectStreamState(max_buffer_size=0, buffer=deque([]), open_send_channels=0, open_receive_channels=1, waiting_receivers=OrderedDict(), waiting_senders=OrderedDict()), _closed=False)

    async def receive(self) -> T_co:
        await checkpoint()
        try:
>           return self.receive_nowait()

/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py:98:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = MemoryObjectReceiveStream(_state=MemoryObjectStreamState(max_buffer_size=0, buffer=deque([]), open_send_channels=0, open_receive_channels=1, waiting_receivers=OrderedDict(), waiting_senders=OrderedDict()), _closed=False)

    def receive_nowait(self) -> T_co:
        """
        Receive the next item if it can be done without waiting.

        :return: the received item
        :raises ~anyio.ClosedResourceError: if this send stream has been closed
        :raises ~anyio.EndOfStream: if the buffer is empty and this stream has been       
            closed from the sending end
        :raises ~anyio.WouldBlock: if there are no items in the buffer and no tasks       
            waiting to send

        """
        if self._closed:
            raise ClosedResourceError

        if self._state.waiting_senders:
            # Get the item from the next sender
            send_event, item = self._state.waiting_senders.popitem(last=False)
            self._state.buffer.append(item)
            send_event.set()

        if self._state.buffer:
            return self._state.buffer.popleft()
        elif not self._state.open_send_channels:
            raise EndOfStream

>       raise WouldBlock
E       anyio.WouldBlock

/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py:93: WouldBlock

During handling of the above exception, another exception occurred:

request = <starlette.requests.Request object at 0x7caa7b7a9d50>

    async def call_next(request: Request) -> Response:
        app_exc: typing.Optional[Exception] = None
        send_stream, recv_stream = anyio.create_memory_object_stream()

        async def receive_or_disconnect() -> Message:
            if response_sent.is_set():
                return {"type": "http.disconnect"}

            async with anyio.create_task_group() as task_group:

                async def wrap(func: typing.Callable[[], typing.Awaitable[T]]) -> T:      
                    result = await func()
                    task_group.cancel_scope.cancel()
                    return result

                task_group.start_soon(wrap, response_sent.wait)
                message = await wrap(request.receive)

            if response_sent.is_set():
                return {"type": "http.disconnect"}

            return message

        async def close_recv_stream_on_response_sent() -> None:
            await response_sent.wait()
            recv_stream.close()

        async def send_no_error(message: Message) -> None:
            try:
                await send_stream.send(message)
            except anyio.BrokenResourceError:
                # recv_stream has been closed, i.e. response_sent has been set.
                return

        async def coro() -> None:
            nonlocal app_exc

            async with send_stream:
                try:
                    await self.app(scope, receive_or_disconnect, send_no_error)
                except Exception as exc:
                    app_exc = exc

        task_group.start_soon(close_recv_stream_on_response_sent)
        task_group.start_soon(coro)

        try:
>           message = await recv_stream.receive()

/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py:78:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = MemoryObjectReceiveStream(_state=MemoryObjectStreamState(max_buffer_size=0, buffer=deque([]), open_send_channels=0, open_receive_channels=1, waiting_receivers=OrderedDict(), waiting_senders=OrderedDict()), _closed=False)

    async def receive(self) -> T_co:
        await checkpoint()
        try:
            return self.receive_nowait()
        except WouldBlock:
            # Add ourselves in the queue
            receive_event = Event()
            container: list[T_co] = []
            self._state.waiting_receivers[receive_event] = container

            try:
                await receive_event.wait()
            except get_cancelled_exc_class():
                # Ignore the immediate cancellation if we already received an item, so as not to
                # lose it
                if not container:
                    raise
            finally:
                self._state.waiting_receivers.pop(receive_event, None)

            if container:
                return container[0]
            else:
>               raise EndOfStream
E               anyio.EndOfStream

/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py:118: EndOfStream

During handling of the above exception, another exception occurred:

self = <app.tests.smoke.test_core_endpoints.TestEndpointPerformance object at 0x7caa819f9a90>
async_test_client = <httpx.AsyncClient object at 0x7caa7b774350>
auth_headers = {'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiN2QzZWY3ZjUtMDc2Mi00MDQwLWFhOTktNGQwOWR...OspxFWjed9UFt1MQh11ycb8o2VKdSlP1X3iADYIocZrpPgRVcV-BCvH3K8_ihEj15GYGoEfhgbWf6wVhlWOrrK6tjtacSpufCgxAT3S5CJNnT75SfHezw'}

    @pytest.mark.asyncio
    async def test_endpoint_response_times(self, async_test_client, auth_headers):        
        """
        Test that key endpoints respond quickly.
        Slow endpoints indicate system issues.
        """
        import time

        performance_targets = [
            ("/health", 100),  # Should respond in <100ms
            ("/api/v1/auth/me", 200),  # Auth check <200ms
        ]

        results = []

        for endpoint, max_ms in performance_targets:
            start = time.time()

            if endpoint == "/health":
                response = await async_test_client.get(endpoint)
            else:
>               response = await async_test_client.get(endpoint, headers=auth_headers)    

app/tests/smoke/test_core_endpoints.py:278:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.11/site-packages/httpx/_client.py:1757: in get
    return await self.request(
/usr/local/lib/python3.11/site-packages/httpx/_client.py:1530: in request
    return await self.send(request, auth=auth, follow_redirects=follow_redirects)
/usr/local/lib/python3.11/site-packages/httpx/_client.py:1617: in send
    response = await self._send_handling_auth(
/usr/local/lib/python3.11/site-packages/httpx/_client.py:1645: in _send_handling_auth     
    response = await self._send_handling_redirects(
/usr/local/lib/python3.11/site-packages/httpx/_client.py:1682: in _send_handling_redirects
    response = await self._send_single_request(request)
/usr/local/lib/python3.11/site-packages/httpx/_client.py:1719: in _send_single_request    
    response = await transport.handle_async_request(request)
/usr/local/lib/python3.11/site-packages/httpx/_transports/asgi.py:162: in handle_async_request
    await self.app(scope, receive, send)
/usr/local/lib/python3.11/site-packages/fastapi/applications.py:1106: in __call__
    await super().__call__(scope, receive, send)
/usr/local/lib/python3.11/site-packages/starlette/applications.py:122: in __call__        
    await self.middleware_stack(scope, receive, send)
/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py:184: in __call__   
    raise exc
/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py:162: in __call__   
    await self.app(scope, receive, _send)
/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py:108: in __call__     
    response = await self.dispatch_func(request, call_next)
app/main.py:173: in swagger_csp_override
    response = await call_next(request)
/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py:84: in call_next     
    raise app_exc
/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py:70: in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
app/core/phi_audit_middleware.py:309: in __call__
    await self.app(scope, receive, send)
/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py:83: in __call__      
    await self.app(scope, receive, send)
/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py:108: in __call__     
    response = await self.dispatch_func(request, call_next)
app/core/security_headers.py:196: in dispatch
    response: StarletteResponse = await call_next(request)
/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py:84: in call_next     
    raise app_exc
/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py:70: in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py:79: in __call__
    raise exc
/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py:68: in __call__
    await self.app(scope, receive, sender)
/usr/local/lib/python3.11/site-packages/fastapi/middleware/asyncexitstack.py:20: in __call__
    raise e
/usr/local/lib/python3.11/site-packages/fastapi/middleware/asyncexitstack.py:17: in __call__
    await self.app(scope, receive, send)
/usr/local/lib/python3.11/site-packages/starlette/routing.py:718: in __call__
    await route.handle(scope, receive, send)
/usr/local/lib/python3.11/site-packages/starlette/routing.py:276: in handle
    await self.app(scope, receive, send)
/usr/local/lib/python3.11/site-packages/starlette/routing.py:66: in app
    response = await func(request)
/usr/local/lib/python3.11/site-packages/fastapi/routing.py:274: in app
    raw_response = await run_endpoint_function(
/usr/local/lib/python3.11/site-packages/fastapi/routing.py:191: in run_endpoint_function  
    return await dependant.call(**values)
app/modules/auth/router.py:414: in get_current_user
    return UserResponse.from_orm(user)
/usr/local/lib/python3.11/site-packages/typing_extensions.py:2360: in wrapper
    return arg(*args, **kwargs)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

cls = <class 'app.modules.auth.schemas.UserResponse'>
obj = <app.core.database_unified.User object at 0x7caa7b7918d0>

    @classmethod
    @typing_extensions.deprecated(
        'The `from_orm` method is deprecated; set '
        "`model_config['from_attributes']=True` and use `model_validate` instead.",       
        category=PydanticDeprecatedSince20,
    )
    def from_orm(cls: type[Model], obj: Any) -> Model:  # noqa: D102
        warnings.warn(
            'The `from_orm` method is deprecated; set `model_config["from_attributes"]=True` '
            'and use `model_validate` instead.',
            DeprecationWarning,
        )
        if not cls.model_config.get('from_attributes', None):
            raise PydanticUserError(
                'You must set the config attribute `from_attributes=True` to use from_orm', code=None
            )
>       return cls.model_validate(obj)
E       pydantic_core._pydantic_core.ValidationError: 1 validation error for UserResponse 
E       role
E         Input should be 'super_admin', 'system_admin', 'security_admin', 'compliance_officer', 'dpo', 'audit_administrator', 'physician', 'attending_physician', 'resident_physician', 'nurse_practitioner', 'registered_nurse', 'lpn', 'clinical_technician', 'pharmacist', 'pharmacy_technician', 'physical_therapist', 'social_worker', 'case_manager', 'patient_registrar', 'medical_records', 'billing_specialist', 'insurance_coordinator', 'appointment_scheduler', 'quality_assurance', 'patient_advocate', 'clinical_researcher', 'data_analyst', 'biostatistician', 'api_client', 'integration_service', 'fhir_client', 'hl7_interface', 'audit_viewer', 'compliance_auditor', 'security_analyst', 'patient', 'patient_proxy', 'caregiver', 'break_glass_provider', 'emergency_responder', 'user', 'admin' or 'operator' [type=enum, input_value='USER', input_type=str]

/usr/local/lib/python3.11/site-packages/pydantic/main.py:1129: ValidationError
--------------------------------- Captured stdout setup ----------------------------------
2025-07-31 00:49:06 [info     ] Security event logged          checksum=a52852a844422c6faf8378bdd19b90651660653484aa00ce92d8a14de00bd92a event_id=ddb00b7581bf660a event_type=token_created expires_at=2025-07-31T01:19:06.295292 jti=408fec78db9ea7b73207c411d3111388 user_id=7d3ef7f5-0762-4040-aa99-4d09df9a0fbb
---------------------------------- Captured stdout call ----------------------------------
2025-07-31 00:49:06 [info     ] CSP configured for development mode allowed_localhost=True unsafe_eval=True
2025-07-31 00:49:06 [debug    ] Security headers relaxed for development mode
2025-07-31 00:49:06 [info     ] Security headers applied       client_ip=127.0.0.1 csp_nonce=/gcBKDu2... headers_applied=['Content-Security-Policy', 'X-Content-Type-Options', 'Referrer-Policy', 'Permissions-Policy', 'Cross-Origin-Embedder-Policy', 'Cross-Origin-Opener-Policy', 'Cross-Origin-Resource-Policy', 'X-Frame-Options', 'X-XSS-Protection', 'X-Permitted-Cross-Domain-Policies', 'Cache-Control', 'Pragma', 'Expires', 'X-Healthcare-Data', 'X-PHI-Protection', 'Report-To'] method=GET path=/health
2025-07-31 00:49:06 [info     ] Security event logged          checksum=d159b4502762fb77cc910ccec2b2818cfaab1d936aba79701632f71c215b16cd event_id=9cadeb45f37943b6 event_type=token_verified jti=408fec78db9ea7b73207c411d3111388 user_id=7d3ef7f5-0762-4040-aa99-4d09df9a0fbb
2025-07-31 00:49:06 [error    ] GLOBAL EXCEPTION on GET /api/v1/auth/me: 1 validation error for UserResponse
role
  Input should be 'super_admin', 'system_admin', 'security_admin', 'compliance_officer', 'dpo', 'audit_administrator', 'physician', 'attending_physician', 'resident_physician', 'nurse_practitioner', 'registered_nurse', 'lpn', 'clinical_technician', 'pharmacist', 'pharmacy_technician', 'physical_therapist', 'social_worker', 'case_manager', 'patient_registrar', 'medical_records', 'billing_specialist', 'insurance_coordinator', 'appointment_scheduler', 'quality_assurance', 'patient_advocate', 'clinical_researcher', 'data_analyst', 'biostatistician', 'api_client', 'integration_service', 'fhir_client', 'hl7_interface', 'audit_viewer', 'compliance_auditor', 'security_analyst', 'patient', 'patient_proxy', 'caregiver', 'break_glass_provider', 'emergency_responder', 'user', 'admin' or 'operator' [type=enum, input_value='USER', input_type=str]
2025-07-31 00:49:06 [error    ] Exception type: ValidationError
2025-07-31 00:49:06 [error    ] Traceback: Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py", line 98, in receive
    return self.receive_nowait()
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py", line 93, in receive_nowait
    raise WouldBlock
anyio.WouldBlock

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py", line 78, in call_next
    message = await recv_stream.receive()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py", line 118, in receive
    raise EndOfStream
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/main.py", line 173, in swagger_csp_override
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/app/app/core/phi_audit_middleware.py", line 309, in __call__
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 83, in __call__
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/core/security_headers.py", line 196, in dispatch
    response: StarletteResponse = await call_next(request)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/usr/local/lib/python3.11/site-packages/fastapi/middleware/asyncexitstack.py", line 20, in __call__
    raise e
  File "/usr/local/lib/python3.11/site-packages/fastapi/middleware/asyncexitstack.py", line 17, in __call__
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 66, in app    
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 274, in app     
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/modules/auth/router.py", line 414, in get_current_user
    return UserResponse.from_orm(user)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/typing_extensions.py", line 2360, in wrapper
    return arg(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/pydantic/main.py", line 1129, in from_orm 
    return cls.model_validate(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/pydantic/main.py", line 503, in model_validate
    return cls.__pydantic_validator__.validate_python(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for UserResponse
role
  Input should be 'super_admin', 'system_admin', 'security_admin', 'compliance_officer', 'dpo', 'audit_administrator', 'physician', 'attending_physician', 'resident_physician', 'nurse_practitioner', 'registered_nurse', 'lpn', 'clinical_technician', 'pharmacist', 'pharmacy_technician', 'physical_therapist', 'social_worker', 'case_manager', 'patient_registrar', 'medical_records', 'billing_specialist', 'insurance_coordinator', 'appointment_scheduler', 'quality_assurance', 'patient_advocate', 'clinical_researcher', 'data_analyst', 'biostatistician', 'api_client', 'integration_service', 'fhir_client', 'hl7_interface', 'audit_viewer', 'compliance_auditor', 'security_analyst', 'patient', 'patient_proxy', 'caregiver', 'break_glass_provider', 'emergency_responder', 'user', 'admin' or 'operator' [type=enum, input_value='USER', input_type=str]


 app/tests/smoke/test_core_endpoints.py::TestEndpointPerformance.test_endpoint_response_times ⨯62% ██████▎   
 app/tests/smoke/test_core_endpoints.py::TestAPIVersioning.test_api_version_in_urls ✓64% ██████▍
 app/tests/smoke/test_isolated_smoke.py::test_python_version ✓              65% ██████▋   
 app/tests/smoke/test_isolated_smoke.py::test_basic_imports ✓               67% ██████▊   
 app/tests/smoke/test_isolated_smoke.py::test_project_imports ✓             69% ██████▉   
 app/tests/smoke/test_isolated_smoke.py::test_config_creation ✓             71% ███████▏  
 app/tests/smoke/test_isolated_smoke.py::test_fastapi_app_import ✓          73% ███████▍  
 app/tests/smoke/test_isolated_smoke.py::test_smoke_test_marker ✓           75% ███████▌  
 app/tests/smoke/test_simple_smoke.py::test_basic_imports ✓                 76% ███████▋  
 app/tests/smoke/test_simple_smoke.py::test_config_loading ✓                78% ███████▊  
 app/tests/smoke/test_simple_smoke.py::test_app_creation ✓                  80% ████████  
 app/tests/smoke/test_simple_smoke.py::test_encryption_service ✓            82% ████████▎ 
 app/tests/smoke/test_simple_smoke.py::test_smoke_marker ✓                  84% ████████▍ 
 app/tests/smoke/test_system_startup.py::TestSystemStartup.test_database_connection ✓85% ████████▋
 app/tests/smoke/test_system_startup.py::TestSystemStartup.test_database_migration_status ✓87% ████████▊ 

―――――――――――――――― TestSystemStartup.test_encryption_service_initialization ――――――――――――――――

self = <app.tests.smoke.test_system_startup.TestSystemStartup object at 0x7caabef0d010>   

    @pytest.mark.order(3)
    @pytest.mark.asyncio
    async def test_encryption_service_initialization(self):
        """
        Verify PHI encryption service is properly configured.
        This is critical for HIPAA compliance.
        """
        encryption_service = EncryptionService()

        # Verify encryption service is configured by testing encryption/decryption        
        # This properly initializes the lazy-loaded cipher_suite
        test_phi = "123-45-6789"  # Test SSN

        # Test that encryption service can encrypt (initializes _fernet)
        try:
            encrypted = await encryption_service.encrypt(test_phi)
            assert encrypted != test_phi, "Value not encrypted"
            assert isinstance(encrypted, str), "Encrypted value should be string"
        except Exception as e:
            pytest.fail(f"Encryption service initialization failed: {e}")

        # Verify cipher suite is now initialized
        assert hasattr(encryption_service, 'cipher_suite'), "Cipher suite not accessible" 
        assert encryption_service.cipher_suite is not None, "Cipher suite not initialized"

        # Test full encryption/decryption cycle
        decrypted = await encryption_service.decrypt(encrypted)
        assert decrypted == test_phi, "Decryption failed"
>       assert encrypted.startswith("gAAAAA"), "Invalid Fernet format"
E       AssertionError: Invalid Fernet format
E       assert False
E        +  where False = <built-in method startswith of str object at 0x62a91d0826a0>('gAAAAA')
E        +    where <built-in method startswith of str object at 0x62a91d0826a0> = 'eyJ2ZXJzaW9uIjogInYyIiwgImFsZ29yaXRobSI6ICJBRVMtMjU2LUdDTSIsICJmaWVsZF90eXBlIjogImdlbmVyaWMiLCAibm9uY2UiOiAicjNYMlNnVDMrY0pNT2tSVSIsICJhYWQiOiAiZXlKbWFXVnNaRjkwZVhCbElqb2dJbWRsYm1WeWFXTWlMQ0FpY0dGMGFXVnVkRjlwWkNJNklHNTFiR3dzSUNKMGFXMWxjM1JoYlhBaU9pQWlNakF5TlMwd055MHpNVlF3TURvME9Ub3dOeTQ1TlRBMU5qa2lmUT09IiwgImRhdGEiOiAid3NRSFpCNFh6Wk82dVVZSXFrY0g4SWh3ZE1sU1RzZVB6MHlGIiwgInRpbWVzdGFtcCI6ICIyMDI1LTA3LTMxVDAwOjQ5OjA3Ljk1MDY5MCIsICJjaGVja3N1bSI6ICI0ZDIxOTUzMWEyZDE4MjRmIn0='.startswith

app/tests/smoke/test_system_startup.py:176: AssertionError

 app/tests/smoke/test_system_startup.py::TestSystemStartup.test_encryption_service_initialization ⨯89% ████████▉ 
 app/tests/smoke/test_system_startup.py::TestSystemStartup.test_redis_connection ✓91% █████████▏
 app/tests/smoke/test_system_startup.py::TestSystemStartup.test_fastapi_app_initialization
 ✓93% █████████▍

―――――――――――――――――― TestSystemStartup.test_audit_service_initialization ―――――――――――――――――――

self = <app.tests.smoke.test_system_startup.TestSystemStartup object at 0x7caabef0e490>   
db_session = <sqlalchemy.ext.asyncio.session.AsyncSession object at 0x7caa803008d0>       

    @pytest.mark.order(6)
    @pytest.mark.asyncio
    async def test_audit_service_initialization(self, db_session: AsyncSession):
        """
        Verify audit logging is operational for SOC2 compliance.
        Every PHI access must be logged.
        """
        audit_service = SOC2AuditService(db_session)

        # Create test audit log
>       test_log = await audit_service.log_action(
            user_id="smoke-test-user",
            action="SYSTEM_HEALTH_CHECK",
            resource_type="system",
            resource_id="smoke-test",
            details={"test": "smoke test audit verification"}
        )

app/tests/smoke/test_system_startup.py:249:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <app.modules.audit_logger.service.SOC2AuditService object at 0x7caa80301c10>       
action = 'SYSTEM_HEALTH_CHECK', user_id = 'smoke-test-user', resource_type = 'system'     
resource_id = 'smoke-test', details = {'test': 'smoke test audit verification'}
kwargs = {}, datetime = <class 'datetime.datetime'>
uuid4 = <function uuid4 at 0x7cab700c6a20>
event = AuditEvent(event_id='f6a919f4-26ee-4a05-8b7e-3f48bf0be207', event_type='SYSTEM_HEALTH_CHECK', aggregate_id='smoke-test...'internal', compliance_tags=['soc2', 'general_audit'], retention_period_days=2555, error_code=None, error_message=None)
success = False

    async def log_action(
        self,
        action: str,
        user_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Log an action for backward compatibility with tests and legacy code.

        This method provides a simplified interface to the comprehensive audit logging    
        system while maintaining SOC2 compliance requirements.
        """
        from datetime import datetime
        from uuid import uuid4

        # Create a basic audit event for the action
        event = AuditEvent(
            event_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            event_type=action,
            aggregate_id=user_id or "system",  # Required by BaseEvent
            aggregate_type="audit_log",        # Required by BaseEvent
            user_id=user_id,
            operation=action,
            outcome="success",
            resource_type=resource_type,
            resource_id=resource_id,
            headers=details or {},
            compliance_tags=["soc2", "general_audit"],
            data_classification="internal",
            publisher="audit_service",
            soc2_category=SOC2Category.SECURITY  # Monitoring Activities
        )

        # Log through the event bus
        success = await self.log_audit_event(event)

        if success:
            # Return a simple object with the expected attributes for tests
            class AuditLogResult:
                def __init__(self, event_data):
                    self.id = event_data.event_id
                    self.timestamp = event_data.timestamp
                    self.user_id = event_data.user_id
                    self.action = event_data.operation
                    self.resource_type = event_data.resource_type
                    self.resource_id = event_data.resource_id

            return AuditLogResult(event)
        else:
>           raise RuntimeError(f"Failed to log audit action: {action}")
E           RuntimeError: Failed to log audit action: SYSTEM_HEALTH_CHECK

app/modules/audit_logger/service.py:937: RuntimeError
---------------------------------- Captured stdout call ----------------------------------
2025-07-31 00:49:08 [error    ] Failed to log audit event      error=Event bus not initialized. Call initialize_event_bus() first. event_id=f6a919f4-26ee-4a05-8b7e-3f48bf0be207    

 app/tests/smoke/test_system_startup.py::TestSystemStartup.test_audit_service_initialization ⨯95% █████████▌
 app/tests/smoke/test_system_startup.py::TestSystemStartup.test_critical_environment_variables ✓96% █████████▋
 app/tests/smoke/test_system_startup.py::TestHealthEndpoints.test_basic_health_endpoint ✓98% █████████▊

――――――――――――――――――― TestHealthEndpoints.test_detailed_health_endpoint ――――――――――――――――――――

self = <app.tests.smoke.test_system_startup.TestHealthEndpoints object at 0x7caabef0f910> 
async_test_client = <httpx.AsyncClient object at 0x7caa8021f9d0>

    @pytest.mark.asyncio
    async def test_detailed_health_endpoint(self, async_test_client):
        """
        Test the detailed health check with component status.
        This verifies all subsystems are operational.
        """
        response = await async_test_client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
>       assert data["status"] == "healthy"
E       AssertionError: assert 'unhealthy' == 'healthy'
E         - healthy
E         + unhealthy
E         ? ++

app/tests/smoke/test_system_startup.py:330: AssertionError
---------------------------------- Captured stdout call ----------------------------------
2025-07-31 00:49:08 [info     ] CSP configured for development mode allowed_localhost=True unsafe_eval=True
2025-07-31 00:49:08 [debug    ] Security headers relaxed for development mode
2025-07-31 00:49:08 [info     ] Security headers applied       client_ip=127.0.0.1 csp_nonce=DDzaoE52... headers_applied=['Content-Security-Policy', 'X-Content-Type-Options', 'Referrer-Policy', 'Permissions-Policy', 'Cross-Origin-Embedder-Policy', 'Cross-Origin-Opener-Policy', 'Cross-Origin-Resource-Policy', 'X-Frame-Options', 'X-XSS-Protection', 'X-Permitted-Cross-Domain-Policies', 'Cache-Control', 'Pragma', 'Expires', 'X-Healthcare-Data', 'X-PHI-Protection', 'Report-To'] method=GET path=/health/detailed

 app/tests/smoke/test_system_startup.py::TestHealthEndpoints.test_detailed_health_endpoint
 ⨯100% ██████████
==================================== warnings summary ====================================
../usr/local/lib/python3.11/site-packages/passlib/utils/__init__.py:854
  /usr/local/lib/python3.11/site-packages/passlib/utils/__init__.py:854: DeprecationWarning: 'crypt' is deprecated and slated for removal in Python 3.13
    from crypt import crypt as _crypt

../usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:268: 26 warnings  
  /usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:268: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.5/migration/
    warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)

../usr/local/lib/python3.11/site-packages/pydantic/_internal/_generate_schema.py:252: 87 warnings
  /usr/local/lib/python3.11/site-packages/pydantic/_internal/_generate_schema.py:252: PydanticDeprecatedSince20: `json_encoders` is deprecated. See https://docs.pydantic.dev/2.5/concepts/serialization/#custom-serializers for alternatives. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.5/migration/
    warnings.warn(

../usr/local/lib/python3.11/site-packages/pydantic/_internal/_fields.py:149
  /usr/local/lib/python3.11/site-packages/pydantic/_internal/_fields.py:149: UserWarning: Field "model_training_category" has conflict with protected namespace "model_".

  You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ()`.
    warnings.warn(

../usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:318
  /usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:318: UserWarning: Valid config keys have changed in V2:
  * 'schema_extra' has been renamed to 'json_schema_extra'
    warnings.warn(message, UserWarning)

../usr/local/lib/python3.11/site-packages/pydantic/fields.py:774
../usr/local/lib/python3.11/site-packages/pydantic/fields.py:774
../usr/local/lib/python3.11/site-packages/pydantic/fields.py:774
../usr/local/lib/python3.11/site-packages/pydantic/fields.py:774
../usr/local/lib/python3.11/site-packages/pydantic/fields.py:774
  /usr/local/lib/python3.11/site-packages/pydantic/fields.py:774: PydanticDeprecatedSince20: `max_items` is deprecated and will be removed, use `max_length` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.5/migration/
    warn('`max_items` is deprecated and will be removed, use `max_length` instead', DeprecationWarning)

../usr/local/lib/python3.11/site-packages/pydantic/_internal/_fields.py:149
  /usr/local/lib/python3.11/site-packages/pydantic/_internal/_fields.py:149: UserWarning: Field "model_version" has conflict with protected namespace "model_".

  You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ()`.
    warnings.warn(

../usr/local/lib/python3.11/site-packages/pydantic/fields.py:768
../usr/local/lib/python3.11/site-packages/pydantic/fields.py:768
../usr/local/lib/python3.11/site-packages/pydantic/fields.py:768
  /usr/local/lib/python3.11/site-packages/pydantic/fields.py:768: PydanticDeprecatedSince20: `min_items` is deprecated and will be removed, use `min_length` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.5/migration/
    warn('`min_items` is deprecated and will be removed, use `min_length` instead', DeprecationWarning)

../usr/local/lib/python3.11/site-packages/pymilvus/client/__init__.py:6
  /usr/local/lib/python3.11/site-packages/pymilvus/client/__init__.py:6: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
    from pkg_resources import DistributionNotFound, get_distribution

../usr/local/lib/python3.11/site-packages/pkg_resources/__init__.py:3146
../usr/local/lib/python3.11/site-packages/pkg_resources/__init__.py:3146
  /usr/local/lib/python3.11/site-packages/pkg_resources/__init__.py:3146: DeprecationWarning: Deprecated call to `pkg_resources.declare_namespace('google')`.
  Implementing implicit namespace packages (as specified in PEP 420) is preferred to `pkg_resources.declare_namespace`. See https://setuptools.pypa.io/en/latest/references/keywords.html#keyword-namespace-packages
    declare_namespace(pkg)

../usr/local/lib/python3.11/site-packages/pkg_resources/__init__.py:3146
  /usr/local/lib/python3.11/site-packages/pkg_resources/__init__.py:3146: DeprecationWarning: Deprecated call to `pkg_resources.declare_namespace('google.logging')`.
  Implementing implicit namespace packages (as specified in PEP 420) is preferred to `pkg_resources.declare_namespace`. See https://setuptools.pypa.io/en/latest/references/keywords.html#keyword-namespace-packages
    declare_namespace(pkg)

../usr/local/lib/python3.11/site-packages/pkg_resources/__init__.py:2558
  /usr/local/lib/python3.11/site-packages/pkg_resources/__init__.py:2558: DeprecationWarning: Deprecated call to `pkg_resources.declare_namespace('google')`.
  Implementing implicit namespace packages (as specified in PEP 420) is preferred to `pkg_resources.declare_namespace`. See https://setuptools.pypa.io/en/latest/references/keywords.html#keyword-namespace-packages
    declare_namespace(parent)

../usr/local/lib/python3.11/site-packages/pkg_resources/__init__.py:3146
../usr/local/lib/python3.11/site-packages/pkg_resources/__init__.py:3146
  /usr/local/lib/python3.11/site-packages/pkg_resources/__init__.py:3146: DeprecationWarning: Deprecated call to `pkg_resources.declare_namespace('zope')`.
  Implementing implicit namespace packages (as specified in PEP 420) is preferred to `pkg_resources.declare_namespace`. See https://setuptools.pypa.io/en/latest/references/keywords.html#keyword-namespace-packages
    declare_namespace(pkg)

app/tests/smoke/test_auth_flow.py:22
  /app/app/tests/smoke/test_auth_flow.py:22: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    pytestmark = pytest.mark.smoke

app/tests/smoke/test_authentication_basic.py:9
  /app/app/tests/smoke/test_authentication_basic.py:9: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.smoke

app/tests/smoke/test_authentication_basic.py:25
  /app/app/tests/smoke/test_authentication_basic.py:25: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.smoke

app/tests/smoke/test_authentication_basic.py:62
  /app/app/tests/smoke/test_authentication_basic.py:62: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.smoke

app/tests/smoke/test_authentication_basic.py:99
  /app/app/tests/smoke/test_authentication_basic.py:99: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.smoke

app/tests/smoke/test_authentication_basic.py:113
  /app/app/tests/smoke/test_authentication_basic.py:113: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.smoke

app/tests/smoke/test_authentication_basic.py:114
  /app/app/tests/smoke/test_authentication_basic.py:114: PytestUnknownMarkWarning: Unknown pytest.mark.security - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.security

app/tests/smoke/test_authentication_basic.py:139
  /app/app/tests/smoke/test_authentication_basic.py:139: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.smoke

app/tests/smoke/test_authentication_basic.py:140
  /app/app/tests/smoke/test_authentication_basic.py:140: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

app/tests/smoke/test_authentication_basic.py:200
  /app/app/tests/smoke/test_authentication_basic.py:200: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.smoke

app/tests/smoke/test_authentication_basic.py:221
  /app/app/tests/smoke/test_authentication_basic.py:221: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.smoke

app/tests/smoke/test_core_endpoints.py:15
  /app/app/tests/smoke/test_core_endpoints.py:15: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    pytestmark = pytest.mark.smoke

app/tests/smoke/test_simple_smoke.py:51
  /app/app/tests/smoke/test_simple_smoke.py:51: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.smoke

app/tests/smoke/test_system_startup.py:22
  /app/app/tests/smoke/test_system_startup.py:22: PytestUnknownMarkWarning: Unknown pytest.mark.smoke - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    pytestmark = pytest.mark.smoke

app/tests/smoke/test_system_startup.py:28
  /app/app/tests/smoke/test_system_startup.py:28: PytestUnknownMarkWarning: Unknown pytest.mark.order - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.order(1)

app/tests/smoke/test_system_startup.py:58
  /app/app/tests/smoke/test_system_startup.py:58: PytestUnknownMarkWarning: Unknown pytest.mark.order - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.order(2)

app/tests/smoke/test_system_startup.py:148
  /app/app/tests/smoke/test_system_startup.py:148: PytestUnknownMarkWarning: Unknown pytest.mark.order - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.order(3)

app/tests/smoke/test_system_startup.py:180
  /app/app/tests/smoke/test_system_startup.py:180: PytestUnknownMarkWarning: Unknown pytest.mark.order - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.order(4)

app/tests/smoke/test_system_startup.py:207
  /app/app/tests/smoke/test_system_startup.py:207: PytestUnknownMarkWarning: Unknown pytest.mark.order - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.order(5)

app/tests/smoke/test_system_startup.py:239
  /app/app/tests/smoke/test_system_startup.py:239: PytestUnknownMarkWarning: Unknown pytest.mark.order - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.order(6)

app/tests/smoke/test_system_startup.py:271
  /app/app/tests/smoke/test_system_startup.py:271: PytestUnknownMarkWarning: Unknown pytest.mark.order - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.order(7)

app/tests/smoke/test_auth_flow.py::TestAuthenticationFlow::test_user_login_success        
  /app/app/modules/auth/router.py:235: PydanticDeprecatedSince20: The `from_orm` method is deprecated; set `model_config['from_attributes']=True` and use `model_validate` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.5/migration/
    user=UserResponse.from_orm(token_data["user"])

app/tests/smoke/test_auth_flow.py::TestAuthenticationFlow::test_user_login_success        
app/tests/smoke/test_core_endpoints.py::TestEndpointPerformance::test_endpoint_response_times
  /usr/local/lib/python3.11/site-packages/pydantic/main.py:1120: PydanticDeprecatedSince20: The `from_orm` method is deprecated; set `model_config["from_attributes"]=True` and use `model_validate` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.5/migration/
    warnings.warn(

app/tests/smoke/test_core_endpoints.py::TestEndpointPerformance::test_endpoint_response_times
  /app/app/modules/auth/router.py:414: PydanticDeprecatedSince20: The `from_orm` method is deprecated; set `model_config['from_attributes']=True` and use `model_validate` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.5/migration/
    return UserResponse.from_orm(user)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================================ short test summary info =================================
FAILED app/tests/smoke/test_auth_flow.py::TestAuthenticationFlow::test_user_login_success - AssertionError: Login failed: {"detail":"Login processing error"}
FAILED app/tests/smoke/test_auth_flow.py::TestAuthenticationFlow::test_login_invalid_credentials - assert 422 == 401
FAILED app/tests/smoke/test_auth_flow.py::TestAuthenticationFlow::test_token_validation_on_protected_endpoint - KeyError: 'access_token'
FAILED app/tests/smoke/test_auth_flow.py::TestAuthenticationFlow::test_access_without_token_fails - assert 403 == 401
FAILED app/tests/smoke/test_auth_flow.py::TestAuthenticationFlow::test_role_based_access_control - KeyError: 'access_token'
FAILED app/tests/smoke/test_auth_flow.py::TestAuthenticationFlow::test_concurrent_sessions - KeyError: 'access_token'
FAILED app/tests/smoke/test_auth_flow.py::TestAuthenticationEdgeCases::test_sql_injection_in_login - assert 422 == 401
FAILED app/tests/smoke/test_core_endpoints.py::TestProtectedEndpoints::test_auth_endpoints - TypeError: 'coroutine' object is not iterable
FAILED app/tests/smoke/test_core_endpoints.py::TestProtectedEndpoints::test_audit_log_endpoints - TypeError: 'coroutine' object is not iterable
FAILED app/tests/smoke/test_core_endpoints.py::TestProtectedEndpoints::test_iris_api_endpoints - TypeError: 'coroutine' object is not iterable
FAILED app/tests/smoke/test_core_endpoints.py::TestEndpointSecurity::test_all_endpoints_require_auth - AssertionError: /api/v1/auth/me not protected!
FAILED app/tests/smoke/test_core_endpoints.py::TestEndpointPerformance::test_endpoint_response_times - pydantic_core._pydantic_core.ValidationError: 1 validation error for UserResponse
FAILED app/tests/smoke/test_system_startup.py::TestSystemStartup::test_encryption_service_initialization - AssertionError: Invalid Fernet format
FAILED app/tests/smoke/test_system_startup.py::TestSystemStartup::test_audit_service_initialization - RuntimeError: Failed to log audit action: SYSTEM_HEALTH_CHECK
FAILED app/tests/smoke/test_system_startup.py::TestHealthEndpoints::test_detailed_health_endpoint - AssertionError: assert 'unhealthy' == 'healthy'

Results (20.93s):
      34 passed
      15 failed
         - app/tests/smoke/test_auth_flow.py:28 TestAuthenticationFlow.test_user_login_success
         - app/tests/smoke/test_auth_flow.py:73 TestAuthenticationFlow.test_login_invalid_credentials
         - app/tests/smoke/test_auth_flow.py:110 TestAuthenticationFlow.test_token_validation_on_protected_endpoint
         - app/tests/smoke/test_auth_flow.py:145 TestAuthenticationFlow.test_access_without_token_fails
         - app/tests/smoke/test_auth_flow.py:167 TestAuthenticationFlow.test_role_based_access_control
         - app/tests/smoke/test_auth_flow.py:324 TestAuthenticationFlow.test_concurrent_sessions
         - app/tests/smoke/test_auth_flow.py:375 TestAuthenticationEdgeCases.test_sql_injection_in_login
         - app/tests/smoke/test_core_endpoints.py:104 TestProtectedEndpoints.test_auth_endpoints
         - app/tests/smoke/test_core_endpoints.py:123 TestProtectedEndpoints.test_audit_log_endpoints
         - app/tests/smoke/test_core_endpoints.py:145 TestProtectedEndpoints.test_iris_api_endpoints
         - app/tests/smoke/test_core_endpoints.py:172 TestEndpointSecurity.test_all_endpoints_require_auth
         - app/tests/smoke/test_core_endpoints.py:257 TestEndpointPerformance.test_endpoint_response_times
         - app/tests/smoke/test_system_startup.py:148 TestSystemStartup.test_encryption_service_initialization
         - app/tests/smoke/test_system_startup.py:239 TestSystemStartup.test_audit_service_initialization
         - app/tests/smoke/test_system_startup.py:320 TestHealthEndpoints.test_detailed_health_endpoint
       6 skipped


Ready for enterprise healthcare operations!
PS C:\Users\aurik\Code_Projects\2_scraper>