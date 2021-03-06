import os
from os.path import join
import utils
from buildercore import core, project, config
from buildercore.utils import first, remove_ordereddict, errcho, lfilter, lmap, isstr
from functools import wraps
from pprint import pformat
import logging

LOG = logging.getLogger(__name__)

from time import time

# http://stackoverflow.com/questions/1622943/timeit-versus-timing-decorator
def timeit(fn):
    @wraps(fn)
    def wrap(*args, **kw):
        ts = time()
        result = fn(*args, **kw)
        te = time()
        LOG.info('func:%r args:[%r, %r] took: %2.4f sec',
                 fn.__name__, args, kw, te - ts)
        return result
    return wrap

def deffile(fname):
    "returns the proper path to the given default file"
    return join(config.TEMP_PATH, fname)

def setdefault(fname, value):
    "writes the given value to the given default file"
    open(deffile(fname), 'w').write(value)

def requires_filtered_project(filterfn=None):
    def wrap1(func):
        @wraps(func)
        def wrap2(_pname=None, *args, **kwargs):
            pname = os.environ.get('PROJECT', _pname) # used by Vagrant ...?
            project_list = project.filtered_projects(filterfn)
            if not pname or not pname.strip() or pname not in project_list:
                pname = utils._pick("project", sorted(project_list), default_file=deffile('.project'))
            return func(pname, *args, **kwargs)
        return wrap2
    return wrap1

# pylint: disable=invalid-name
requires_project = requires_filtered_project(None)

def requires_aws_project_stack(*plist):
    if not plist:
        plist = [utils._pick("project", project.project_list(), default_file=deffile('.project'))]

    def wrap1(func):
        @wraps(func)
        def _wrapper(stackname=None, *args, **kwargs):
            region = utils.find_region(stackname)
            asl = core.active_stack_names(region)
            if not asl:
                print('\nno AWS stacks exist, cannot continue.')
                return

            def pname_startswith(stack):
                for pname in plist:
                    if stack.startswith(pname):
                        return stack
            asl = lfilter(pname_startswith, asl)
            if not stackname or stackname not in asl:
                stackname = utils._pick("stack", asl)
            return func(stackname, *args, **kwargs)
        return _wrapper
    return wrap1

def requires_aws_stack(func):
    @wraps(func)
    def call(*args, **kwargs):
        stackname = first(args) or os.environ.get('INSTANCE')
        region = utils.find_region(stackname)
        if stackname:
            args = args[1:]
            return func(stackname, *args, **kwargs)
        # note: this assumes all stacks have an ec2 instance.
        asl = core.active_stack_names(region)
        if not asl:
            raise RuntimeError('\nno AWS stacks *in an active state* exist, cannot continue.')
        if not stackname or stackname not in asl:
            stackname = utils._pick("stack", asl, default_file=deffile('.active-stack'))
        args = args[1:]
        return func(stackname, *args, **kwargs)
    return call

def requires_steady_stack(func):
    @wraps(func)
    def call(*args, **kwargs):
        ss = core.steady_aws_stacks(utils.find_region())
        keys = lmap(first, ss)
        idx = dict(zip(keys, ss))
        helpfn = lambda pick: idx[pick][1]
        if not keys:
            print('\nno AWS stacks *in a steady state* exist, cannot continue.')
            return
        stackname = first(args) or os.environ.get('INSTANCE')
        if not stackname or stackname not in keys:
            stackname = utils._pick("stack", sorted(keys), helpfn=helpfn, default_file=deffile('.active-stack'))
        return func(stackname, *args[1:], **kwargs)
    return call

def echo_output(func):
    "pretty-prints the return value of the task(s) being run to stdout"
    @wraps(func)
    def _wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        errcho('output:') # printing to stderr avoids corrupting structured data
        if isstr(res):
            print(res)
        else:
            print(pformat(remove_ordereddict(res)))
        return res
    return _wrapper
