__all__ = [
    'QueryFieldsMixin',
    'SerpyQueryFieldsMixin',
]

class BaseFieldsMixin(object):

    # If using Django filters in the API, these labels mustn't conflict with any model field names.
    include_arg_name = 'fields'
    exclude_arg_name = 'fields!'

    # Split field names by this string.  It doesn't necessarily have to be a single character.
    # Avoid RFC 1738 reserved characters i.e. ';', '/', '?', ':', '@', '=' and '&'
    delimiter = ','

    def __init__(self, *args, **kwargs):

        if not hasattr(self, '_fields_attribute'):
            raise AttributeError("Derived classes must set the '_fields_attribute' class variable.")
        super(BaseFieldsMixin, self).__init__(*args, **kwargs)
        self._sieve_fieldset()

    @property
    def _fields(self):
        """
        Returns the fields attribute as specified in derived classes.
        """
        return getattr(self, self._fields_attribute)

    def _get_request_method(self):
        """
        Returns the request method.
        """
        request = self.context['request']
        method = request.method
        if method != 'GET':
            raise AttributeError
        return (request, method)

    def _get_query_params(self, request):
        """
        Returns the query parameters for the request if, and only if, the
        request method is GET.
        """
        return getattr(request, 'query_params') or getattr(request, 'QUERY_PARAMS', request.GET)

    def _get_fieldsets(self):
        """
        Returns the included and excluded field names.
        """
        _get_field_names = lambda fieldset: {
            fname for fnames in fieldset for fname fnames.split(self.delimiter) if fname
        }
        included = _get_field_names(query_params.getlist(self.include_arg_name))
        excluded = _get_field_names(query_params.getlist(self.exclude_arg_name))
        return (included, excluded)

    def _drop_fields(self, included, excluded):
        """
        Drops the fields that are specified by the request, if necessary.
        """
        fields = self._fields
        serializer_fields = set(fields)
        fields_to_drop = serializer_fields & excluded
        if included:
            fields_to_drop |= serializer_fields - included
        for field in fields_to_drop:
            fields.pop(field)

    def _sieve_fieldset(self):
        """
        Performs sieving of the serializers fieldset based upon the request, if necessary.
        """
        try:
            request, method = self._get_request_method()
            query_params = self._get_query_params(request)
        except (AttributeError, TypeError, KeyError):
            return
        included, excluded = self._get_fieldsets()
        if not (included or excluded):
            return
        self._drop_fields(included, excluded)

class QueryFieldsMixin(BaseFieldsMixin):
    """
    Provides a mixin for dynamic fields on the Django Rest Frameworks
    serializer instances.
    """
    _fields_attribute = 'fields'

class SerpyQueryFieldsMixin(BaseFieldsMixin):
    """
    Provides a mixin for dynamic fields on serpy's implementation(s)
    of serializtion in place of Django Rest Frameworks serializers.
    """
    _fields_attribute = '_compiled_fields'
