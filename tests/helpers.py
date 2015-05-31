import os
import os.path
import shutil
import sys
import tempfile
import time
import unittest

DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.dirname(DIR))

_temp_dirs = []


def make_temp_dir():
    path = tempfile.mkdtemp(dir=DIR)
    _temp_dirs.append(path)
    return path


def wait_for_job(job, secs=1):
    for i in xrange(secs * 10):
        if not job.is_running():
            return job
        time.sleep(0.1)
    raise AssertionError('wait_for_job timed out')


def clean():
    for path in _temp_dirs:
        shutil.rmtree(path)
    _temp_dirs[:] = []


def read_file(path):
    with open(path) as f:
        return f.read()


def _update_env(vals):
    for k, v in vals.iteritems():
        if v is None:
            del os.environ[k]
        else:
            os.environ[k] = v


class _OnExit(object):
    def __init__(self, f, *args, **kwargs):
        self._f = f
        self._args = args
        self._kwargs = kwargs

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._f(*self._args, **self._kwargs)


def update_env(**vals):
    old = dict((k, os.environ.get(k)) for k in vals.iterkeys())
    _update_env(vals)
    return _OnExit(_update_env, old)


def main():
    try:
        unittest.main()
    finally:
        clean()