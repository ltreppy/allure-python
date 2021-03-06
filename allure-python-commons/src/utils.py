# -*- coding: utf-8 -*-

import os
import sys
import six
import time
import uuid
import socket
import inspect
import hashlib
import platform
import threading
import traceback

if sys.version_info.major > 2:
    from traceback import format_exception_only
else:
    from _compat import format_exception_only


def md5(*args):
    m = hashlib.md5()
    for arg in args:
        part = arg.encode('utf-8')
        m.update(part)
    return m.hexdigest()


def uuid4():
    return str(uuid.uuid4())


def now():
    return int(round(1000 * time.time()))


def platform_label():
    major_version, _, __ = platform.python_version_tuple()
    implementation = platform.python_implementation()
    return '{implementation}{major_version}'.format(implementation=implementation.lower(),
                                                    major_version=major_version)


def thread_tag():
    return '{0}-{1}'.format(os.getpid(), threading.current_thread().name)


def host_tag():
    return socket.gethostname()


def represent(item):
    """
    >>> represent(None)
    'None'

    >>> represent(123)
    '123'

    >>> from sys import version_info
    >>> expected = u"'hi'" if version_info.major < 3 else "'hi'"
    >>> represent('hi') == expected
    True

    >>> from sys import version_info
    >>> expected = u"'привет'" if version_info.major < 3 else "'привет'"
    >>> represent(u'привет') == expected
    True

    >>> represent(bytearray([0xd0, 0xbf]))  # doctest: +ELLIPSIS
    "<... 'bytearray'>"

    >>> from struct import pack
    >>> result = "<type 'str'>" if version_info.major < 3 else "<class 'bytes'>"
    >>> represent(pack('h', 0x89)) == result
    True

    >>> result = "<type 'int'>" if version_info.major < 3 else "<class 'int'>"
    >>> represent(int) == result
    True

    >>> represent(represent)  # doctest: +ELLIPSIS
    '<function represent at ...>'

    >>> represent([represent])  # doctest: +ELLIPSIS
    '[<function represent at ...>]'

    >>> class ClassWithName(object):
    ...     pass

    >>> represent(ClassWithName)
    "<class 'utils.ClassWithName'>"
    """

    if sys.version_info.major < 3 and isinstance(item, str):
        try:
            item = item.decode(encoding='UTF-8')
        except UnicodeDecodeError:
            pass

    if isinstance(item, six.text_type):
        return u'\'%s\'' % item
    elif isinstance(item, (bytes, bytearray)):
        return repr(type(item))
    else:
        return repr(item)


def func_parameters(func, *args, **kwargs):
    """
    >>> def helper(func):
    ...     def wrapper(*args, **kwargs):
    ...         params = func_parameters(func, *args, **kwargs)
    ...         print(sorted(params.items()))
    ...         return func(*args, **kwargs)
    ...     return wrapper

    >>> @helper
    ... def args(a, b):
    ...     pass

    >>> args(1, 2)
    [('a', '1'), ('b', '2')]

    >>> args(*(1,2))
    [('a', '1'), ('b', '2')]

    >>> args(1, b=2)
    [('a', '1'), ('b', '2')]

    >>> @helper
    ... def kwargs(a=1, b=2):
    ...     pass

    >>> kwargs()
    [('a', '1'), ('b', '2')]

    >>> kwargs(a=3, b=4)
    [('a', '3'), ('b', '4')]

    >>> kwargs(b=4, a=3)
    [('a', '3'), ('b', '4')]

    >>> kwargs(a=3)
    [('a', '3'), ('b', '2')]

    >>> kwargs(b=4)
    [('a', '1'), ('b', '4')]

    >>> @helper
    ... def args_kwargs(a, b, c=3, d=4):
    ...     pass

    >>> args_kwargs(1, 2)
    [('a', '1'), ('b', '2'), ('c', '3'), ('d', '4')]

    >>> args_kwargs(1, 2, d=5)
    [('a', '1'), ('b', '2'), ('c', '3'), ('d', '5')]

    >>> args_kwargs(1, 2, 5, 6)
    [('a', '1'), ('b', '2'), ('c', '5'), ('d', '6')]

    >>> @helper
    ... def varargs(*a):
    ...     pass

    >>> varargs()
    []

    >>> varargs(1, 2)
    [('a', '(1, 2)')]

    >>> @helper
    ... def keywords(**a):
    ...     pass

    >>> keywords()
    []

    >>> keywords(a=1, b=2)
    [('a', '1'), ('b', '2')]

    >>> @helper
    ... def args_varargs(a, b, *c):
    ...     pass

    >>> args_varargs(1, 2)
    [('a', '1'), ('b', '2')]

    >>> args_varargs(1, 2, 2)
    [('a', '1'), ('b', '2'), ('c', '(2,)')]

    >>> @helper
    ... def args_kwargs_varargs(a, b, c=3, **d):
    ...     pass

    >>> args_kwargs_varargs(1, 2)
    [('a', '1'), ('b', '2'), ('c', '3')]

    >>> args_kwargs_varargs(1, 2, 4, d=5, e=6)
    [('a', '1'), ('b', '2'), ('c', '4'), ('d', '5'), ('e', '6')]

    >>> @helper
    ... def args_kwargs_varargs_keywords(a, b=2, *c, **d):
    ...     pass


    >>> args_kwargs_varargs_keywords(1)
    [('a', '1'), ('b', '2')]

    >>> args_kwargs_varargs_keywords(1, 2, 4, d=5, e=6)
    [('a', '1'), ('b', '2'), ('c', '(4,)'), ('d', '5'), ('e', '6')]


    >>> class Class(object):
    ...     @staticmethod
    ...     @helper
    ...     def static_args(a, b):
    ...         pass
    ...
    ...     @classmethod
    ...     @helper
    ...     def method_args(cls, a, b):
    ...         pass
    ...
    ...     @helper
    ...     def args(self, a, b):
    ...         pass

    >>> cls = Class()

    >>> cls.args(1, 2)
    [('a', '1'), ('b', '2')]

    >>> cls.method_args(1, 2)
    [('a', '1'), ('b', '2')]

    >>> cls.static_args(1, 2)
    [('a', '1'), ('b', '2')]

    """
    parameters = {}
    arg_spec = inspect.getargspec(func) if sys.version_info.major < 3 else inspect.getfullargspec(func)
    args_dict = dict(zip(arg_spec.args, args))

    if arg_spec.defaults:
        kwargs_defaults_dict = dict(zip(arg_spec.args[len(args):], arg_spec.defaults))
        parameters.update(kwargs_defaults_dict)

    if arg_spec.varargs:
        varargs = args[len(arg_spec.args):]
        parameters.update({arg_spec.varargs: varargs} if varargs else {})

    if arg_spec.args and arg_spec.args[0] in ['cls', 'self']:
        args_dict.pop(arg_spec.args[0], None)

    parameters.update(kwargs)
    parameters.update(args_dict)

    items = parameters.iteritems() if sys.version_info.major < 3 else parameters.items()
    return dict(map(lambda kv: (kv[0], represent(kv[1])), items))


def format_traceback(exc_traceback):
    return ''.join(traceback.format_tb(exc_traceback)) if exc_traceback else None


def format_exception(etype, value):
    """
    >>> import sys

    >>> try:
    ...     assert False, u'Привет'
    ... except AssertionError:
    ...     etype, e, _ = sys.exc_info()
    ...     format_exception(etype, e) # doctest: +ELLIPSIS
    'AssertionError: ...\\n'

    >>> try:
    ...     assert False, 'Привет'
    ... except AssertionError:
    ...     etype, e, _ = sys.exc_info()
    ...     format_exception(etype, e) # doctest: +ELLIPSIS
    'AssertionError: ...\\n'

    >>> try:
    ...    compile("bla u'Привет'", "fake.py", "exec")
    ... except SyntaxError:
    ...    etype, e, _ = sys.exc_info()
    ...    format_exception(etype, e) # doctest: +ELLIPSIS
    '  File "fake.py", line 1...SyntaxError: invalid syntax\\n'

    >>> try:
    ...    compile("bla 'Привет'", "fake.py", "exec")
    ... except SyntaxError:
    ...    etype, e, _ = sys.exc_info()
    ...    format_exception(etype, e) # doctest: +ELLIPSIS
    '  File "fake.py", line 1...SyntaxError: invalid syntax\\n'

    >>> from hamcrest import assert_that, equal_to

    >>> try:
    ...     assert_that('left', equal_to('right'))
    ... except AssertionError:
    ...     etype, e, _ = sys.exc_info()
    ...     format_exception(etype, e) # doctest: +ELLIPSIS
    "AssertionError: \\nExpected:...but:..."

    >>> try:
    ...     assert_that(u'left', equal_to(u'right'))
    ... except AssertionError:
    ...     etype, e, _ = sys.exc_info()
    ...     format_exception(etype, e) # doctest: +ELLIPSIS
    "AssertionError: \\nExpected:...but:..."
    """
    return '\n'.join(format_exception_only(etype, value)) if etype or value else None
