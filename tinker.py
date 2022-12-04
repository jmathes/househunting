# Copyright (c) 2011, 2012, 2013, 2014 Sauce Labs Inc
# Authors: Joe Mathes
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import builtins
import datetime
import inspect
import logging
import re
import traceback
from pprint import pformat
from typing import Sized, cast

# Listen up, you primitives! This is my BOOM stick
primitives = [tuple, list, set, dict, int, float, str, bool]


# TODO: add or import tests


def get_fn_args(function):
    if inspect.isclass(function):
        return "<parents>"
    members = dict(get_members(function))
    if "__code__" not in members:
        if "__func__" not in members:
            return "<unknown signature>"
        members = dict(get_members(members["__func__"]))
    return ", ".join(members["__code__"].co_varnames)


def get_instancemethod_source(method, filename=None):
    definition = (
        f"Tinker can't locate definition of {method}. Usually that means "
        "it's compiled or created in an unusual way, like lambda or "
        "functools.partial."
    )
    try:
        inspected_method = inspect.getmodule(method)
        if inspected_method is not None:
            definition = f"from {inspected_method.__file__}"
            try:
                definition += f":{inspect.getsourcelines(method)[1]}"
            except TypeError:
                pass
    except AttributeError:
        pass
    except ValueError:
        pass
    except OSError:
        pass
    return definition


def wrap_with_delimiters(summary, tb, lines):
    time = datetime.datetime.utcnow().strftime("%H:%M:%S.%f")
    ad_for_self = f" {summary} @ {tb[-2][0]}:{tb[-2][1]} [{time} utc] "
    delim_bar_len = min(max(len(lines[0]) + 3, len(ad_for_self) + 10), 150)
    delim_bar_chunk = "=" * (delim_bar_len - len(ad_for_self) - 2)
    delim_bar = "==" + ad_for_self + delim_bar_chunk
    if delim_bar_len >= 150:
        delim_bar += " ... "

    var_dump = "\n/" + delim_bar + "\\\n"
    for line in lines:
        sub_lines = ["| " + subline for subline in line.split("\n")]
        var_dump += "\n".join(sub_lines) + "\n"
    var_dump += "\\" + delim_bar + "/\n"
    return var_dump


def get_parents(klass):
    def iterate_through_tree(iterable, collected):
        for node in iterable:
            if isinstance(node, tuple) or isinstance(node, list):
                iterate_through_tree(node, collected)
            elif node.__name__ not in collected and node is not object and node is not klass:
                collected.append(node.__name__)

    collected = []
    iterate_through_tree(inspect.getclasstree([klass]), collected)
    return collected


def get_members(object, predicate=None):
    """Return all members of an object as (name, value) pairs sorted by name.
    Optionally, only return members that satisfy a given predicate.

    Copypasta'd from inspect bc they don't handle exceptions gracefully
    (https://bugs.python.org/issue35108)
    """

    if inspect.isclass(object):
        mro = (object,) + inspect.getmro(object)

    else:
        mro = ()

    results = []

    processed = set()

    names = dir(object)

    # :dd any DynamicClassAttributes to the list of names if object is a class;
    # this may result in duplicate entries if, for example, a virtual
    # attribute with the same name as a DynamicClassAttribute exists

    try:

        for base in object.__bases__:

            for k, v in base.__dict__.items():

                if isinstance(v, inspect.types.DynamicClassAttribute):  # type: ignore

                    names.append(k)

    except AttributeError:

        pass

    for key in names:

        # First try to get the value via getattr.  Some descriptors don't
        # like calling their __get__ (see bug #1785), so fall back to
        # looking in the __dict__.
        try:

            try:
                value = getattr(object, key)
            except Exception as e:
                value = e
            # handle the duplicate key

            if key in processed:

                raise AttributeError

        except AttributeError:

            for base in mro:

                if key in base.__dict__:

                    value = base.__dict__[key]

                    break
            else:

                # could be a (currently) missing slot member, or a buggy
                # __dir__; discard and move on
                continue

        if not predicate or predicate(value):

            results.append((key, value))

        processed.add(key)

    results.sort(key=lambda pair: pair[0])

    return results


def get_pretty_debug_output(tb, value=None, my_name=None, my_type=None):
    def get_attribute(value, attr):
        try:
            return getattr(value, attr)
        except AttributeError:
            try:
                return value.__getattribute__(attr)
            except Exception as e:
                return e
        except Exception as e:
            return e

    lines = []
    try:
        my_type = value.__class__.__name__
    except AttributeError:
        pass
    if my_type is None:
        my_type = type(value).__name__
    if my_name is None:
        my_name = tb[-1][2]
    call = tb[-2][3] or my_name + "(<from repl>)"
    exp = re.search(my_name + r"\((.*)\)", call)
    if exp:
        exp = exp.groups()[0]
        exp = f"{my_name}({exp})"
    else:
        exp = call

    docstring_lines = []
    if isinstance(value.__doc__, str):
        docstring_lines = ["#  " + label for label in value.__doc__.split("\n")]

    members = dict(get_members(value))

    if any((type(value) is t) for t in primitives):
        lines += pformat(value).split("\n")
    elif my_type == "function":
        lines += docstring_lines
        lines.append(f"{members['__qualname__']}({get_fn_args(value)})")
        lines.append(f"from {members['__code__'].co_filename}:{members['__code__'].co_firstlineno}")
    elif my_type == "traceback":
        lines += [line[:-1] for line in traceback.format_tb(value)]
    elif my_type == "method" or my_type == "instancemethod":
        lines += docstring_lines
        func_members = dict(get_members(members["__func__"]))
        lines.append(f"{func_members['__qualname__']}({get_fn_args(members['__func__'])})")
        lines.append(get_instancemethod_source(value, members.get("__file__", None)))
    else:
        if my_type == "type":
            assert value is not None
            lines += docstring_lines
            lines.append(f"class {value.__name__} from {value.__module__}")
            if hasattr(value, "__implemented__"):
                assert value is not None
                lines.append(str(value.__implemented__))
            lines.append("inherited from:")
            lines += pformat(get_parents(value)).split("\n")
        lines += docstring_lines

        max_len = 0
        callables = []
        uncallables = []
        attributes = [v for v in dir(value) if not v.startswith("__")]
        for attr_name in attributes:
            attr = get_attribute(value, attr_name)
            if True and type(attr).__name__ != "classobj" and callable(attr):
                max_len = max(max_len, len(attr_name))
                callables.append((attr, attr_name))
            else:
                max_len = max(max_len, len(attr_name))
                uncallables.append((attr, attr_name))
        full_spaces = " " * (max_len + 5)

        for attr, attr_name in uncallables:
            spaces = " " * (max_len - len(attr_name) + 3)
            try:
                formatted_attr = pformat(attr)
            except Exception as e:
                argslist = ",".join(map(pformat, e.args))
                if len(argslist) > 60:
                    argslist = argslist[:60] + "..."
                formatted_attr = f"<raised {e.__class__.__name__}({argslist})"
            new_lines = (f".{attr_name}:{spaces}{formatted_attr}").split("\n")
            lines.append(new_lines[0])
            for line in new_lines[1:]:
                lines.append(full_spaces + line)
        for attr, attr_name in callables:
            spaces = " " * (max_len - len(attr_name))
            instances = get_instancemethod_source(attr, members.get("__file__", None))
            lines.append(f".{attr_name}(): {spaces}{instances}")
            if attr.__doc__ is not None:
                docstring = attr.__doc__.split("\n")
                docstring.reverse()
                first_line = str(docstring.pop().strip())
                while first_line == "" and docstring:
                    first_line = str(docstring.pop().lstrip())
                if len(docstring) > 0:
                    first_line += f"... ({len(docstring)} more line{'' if len(docstring) == 1 else 's'})"
                lines.append(full_spaces + "# " + first_line)

        if hasattr(value, "__traceback__"):
            assert value is not None
            lines.append("         --- traceback ---")
            lines += [line[:-1] for line in traceback.format_tb(value.__traceback__)]

    if len(lines) == 0:
        try:
            lines += pformat(value.__dict__).split("\n")
        except AttributeError:
            lines += pformat(value).split("\n")
    if any(isinstance(value, t) for t in [list, tuple, dict, str]):
        my_type += f"[{len(cast(Sized, value))}]"

    return wrap_with_delimiters(f"{exp} :: {my_type}", tb, lines)


def decide_value(args):
    if len(args) == 0:
        return None
    elif len(args) > 1:
        return args
    else:
        return args[0]


def log(*args):
    tb = traceback.extract_stack()  # Pls don't refactor extract_stack out of this function.
    # It will mess up the traceback, even if you adjust how
    # the traceback is used; it'll mess up other stuff.
    value = decide_value(args)
    detailed_description = get_pretty_debug_output(tb, value)
    logging.error(detailed_description)
    return value


def dump(*args):
    tb = traceback.extract_stack()  # Pls don't refactor extract_stack out of this function.
    # It will mess up the traceback, even if you adjust how
    # the traceback is used; it'll mess up other stuff.
    value = decide_value(args)
    detailed_description = get_pretty_debug_output(tb, value)
    print(detailed_description)
    return value


def die(*args, **kwargs):
    exit_code = 1
    if "exit_code" in kwargs:
        exit_code = kwargs["exit_code"]
    tb = traceback.extract_stack()
    logging.error(get_pretty_debug_output(tb, decide_value(args)))
    exit(exit_code)


def format(*args):
    tb = traceback.extract_stack()  # Pls don't refactor extract_stack out of this function.
    # It will mess up the traceback, even if you adjust how
    # the traceback is used; it'll mess up other stuff.
    return get_pretty_debug_output(tb, decide_value(args))


def log_trace():
    # Pls don't DRY this with dump_trace. Makes the traceback less readable
    tb = traceback.extract_stack()
    formatted_traceback = wrap_with_delimiters("runtime stack trace", tb, ["".join(traceback.format_list(tb))[:-1]])
    logging.error(formatted_traceback)
    return formatted_traceback


def dump_trace():
    tb = traceback.extract_stack()  # Pls don't refactor extract_stack out of this function.
    # It will mess up the traceback, even if you adjust how
    # the traceback is used; it'll mess up other stuff.
    formatted_traceback = wrap_with_delimiters("runtime stack trace", tb, ["".join(traceback.format_list(tb))[:-1]])

    return formatted_traceback


all = [
    die,
    dump,
    dump_trace,
    format,
    log,
    log_trace,
]


__all__ = [util.__name__ for util in all]  # type: ignore


def export_all(prefix="t"):
    for util in all:
        setattr(builtins, prefix + util.__name__, util)
