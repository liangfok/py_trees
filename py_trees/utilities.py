#!/usr/bin/env python
#
# License: BSD
#   https://raw.githubusercontent.com/splintered-reality/py_trees/devel/LICENSE
#
##############################################################################
# Documentation
##############################################################################

"""
Assorted utility functions.
"""

##############################################################################
# Imports
##############################################################################

import multiprocessing
import os
import re
import traceback
import typing

##############################################################################
# Python Helpers
##############################################################################


def static_variables(**kwargs):
    """
    Attach initialised static variables to a python method.

    .. code-block:: python

       @static_variables(counter=0)
       def foo():
           foo.counter += 1
           print("Counter: {}".format(foo.counter))
    """
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


@static_variables(primitives={bool, str, int, float})
def is_primitive(incoming: typing.Any) -> bool:
    """
    Check if an incoming argument is a primitive type with no esoteric accessors.

    That is, it has no class attributes or container style [] accessors.

    Args:
        incoming: the instance to check
    Returns:
        True or false, depending on the check against the reserved primitives
    """
    return type(incoming) in is_primitive.primitives


def truncate(original: str, length: int) -> str:
    """
    Provide an elided (...) version of a string if it is longer than desired.

    Args:
        original: string to elide
        length: constrain the elided string to this
    """
    s = (original[:length - 3] + '...') if len(original) > length else original
    return s

##############################################################################
# System Tools
##############################################################################


class Process(multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self._pconn, self._cconn = multiprocessing.Pipe()
        self._exception = None

    def run(self):
        try:
            multiprocessing.Process.run(self)
            self._cconn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._cconn.send((e, tb))

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception


def which(program):
    """
    Call the command line 'which' tool (convenience wrapper).

    Args:
        program (:obj:`str`): name of the program to find.

    Returns:
        :obj:`str`: path to the program or None if it doesnt exist.
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, unused_fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def get_valid_filename(s: str) -> str:
    """
    Clean up and style a string so that it can be used as a filename.

    This is valid only from the perspective of the py_trees package. It does
    place a few extra constraints on strings to keep string handling and
    manipulation complexities to a minimum so that sanity prevails.

    * Removes leading and trailing spaces
    * Convert other spaces and newlines to underscores
    * Remove anything that is not an alphanumeric, dash, underscore, or dot

    .. code-block:: python

        >>> utilities.get_valid_filename("john's portrait in 2004.jpg")
        'johns_portrait_in_2004.jpg'

    Args:
        program (:obj:`str`): string to convert to a valid filename

    Returns:
        :obj:`str`: a representation of the specified string as a valid filename
    """
    s = str(s).strip().lower().replace(' ', '_').replace('\n', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def get_fully_qualified_name(instance: object) -> str:
    """
    Retrieve the fully qualified name of an object.

    For example, an instance of
    :class:`~py_trees.composites.Sequence` becomes 'py_trees.composites.Sequence'.

    Args:
        instance (:obj:`object`): an instance of any class

    Returns:
        :obj:`str`: the fully qualified name
    """
    module = instance.__class__.__module__
    # if there is no module, it will report builtin, get that
    # string via what should remain constant, the 'str' class
    # and check against that.
    builtin = str.__class__.__module__
    if module is None or module == builtin:
        return instance.__class__.__name__
    else:
        return module + '.' + instance.__class__.__name__
