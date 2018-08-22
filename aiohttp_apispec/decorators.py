from apispec.ext.marshmallow.swagger import schema2parameters


def docs(**kwargs):
    """
    Annotate the decorated view function with the specified Swagger
    attributes.

    Usage:

    .. code-block:: python

        from aiohttp import web

        @docs(tags=['my_tag'],
              summary='Test method summary',
              description='Test method description')
        async def index(request):
            return web.json_response({'msg': 'done', 'data': {}})

    """

    def wrapper(func):
        kwargs['produces'] = ['application/json']
        if not hasattr(func, '__apispec__'):
            func.__apispec__ = {'parameters': [], 'responses': {}, 'docked': {}}
        func.__apispec__.update(kwargs)
        func.__apispec__['docked'] = {'route': False}
        return func

    return wrapper


def use_kwargs(schema, locations=None, **kwargs):
    """
    Add request info into the swagger spec and
    prepare injection keyword arguments from the specified
    webargs arguments into the decorated view function in
    request['data'] for aiohttp_apispec_middleware validation middleware.

    Usage:

    .. code-block:: python

        from aiohttp import web
        from marshmallow import Schema, fields


        class RequestSchema(Schema):
            id = fields.Int()
            name = fields.Str(description='name')

        @use_kwargs(RequestSchema(strict=True))
        async def index(request):
            # aiohttp_apispec_middleware should be used for it
            data = request['data']
            return web.json_response({'name': data['name'],
                                      'id': data['id']})

    :param schema: :class:`Schema <marshmallow.Schema>` class or instance
    :param locations: Default request locations to parse
    """
    if callable(schema):
        schema = schema()
    # location kwarg added for compatibility with old versions
    locations = locations or []
    if not locations:
        locations = kwargs.get('location')
        if locations:
            locations = [locations]
        else:
            locations = None

    options = {'required': kwargs.get('required', False)}
    if locations:
        options['default_in'] = locations[0]

    def wrapper(func):
        parameters = schema2parameters(schema, **options)
        if not hasattr(func, '__apispec__'):
            func.__apispec__ = {'parameters': [], 'responses': {}, 'docked': {}}
        func.__apispec__['parameters'].extend(parameters)
        if not hasattr(func, '__schemas__'):
            func.__schemas__ = []
        func.__schemas__.append({'schema': schema, 'locations': locations})

        return func

    return wrapper


def marshal_with(schema, code=200, required=False, description=None):
    """
    Add response info into the swagger spec

    Usage:

    .. code-block:: python

        from aiohttp import web
        from marshmallow import Schema, fields


        class ResponseSchema(Schema):
            msg = fields.Str()
            data = fields.Dict()

        @marshal_with(ResponseSchema(), 200)
        async def index(request):
            return web.json_response({'msg': 'done', 'data': {}})

    :param schema: :class:`Schema <marshmallow.Schema>` class or instance
    :param code: HTTP response code
    """
    if callable(schema):
        schema = schema()

    def wrapper(func):
        if not hasattr(func, '__apispec__'):
            func.__apispec__ = {'parameters': [], 'responses': {}, 'docked': {}}
        raw_parameters = schema2parameters(schema, required=required)[0]
        # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#responseObject
        valid_response_fields = ('schema', 'description', 'headers', 'examples')
        parameters = {k: v for k, v in raw_parameters.items() if k in valid_response_fields}
        if description:
            parameters['description'] = description
        func.__apispec__['responses']['%s' % code] = parameters
        return func

    return wrapper
