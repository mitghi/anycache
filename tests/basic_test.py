from pathlib import Path
from tempfile import mkdtemp

from nose.tools import eq_

from anycache import AnyCache
from anycache import get_defaultcache
from anycache import anycache


def test_basic():
    """Basic functionality."""

    @anycache()
    def myfunc(posarg, kwarg=3):
        # count the number of calls
        myfunc.callcount += 1
        return posarg + kwarg
    myfunc.callcount = 0

    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 1)
    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 1)
    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 1)
    eq_(myfunc(4, 2), 6)
    eq_(myfunc.callcount, 2)
    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 2)

    assert get_defaultcache().size > 0


def test_del():
    ac = AnyCache()

    @ac.anycache()
    def myfunc(posarg, kwarg=3):
        return posarg + kwarg

    eq_(myfunc(4, 5), 9)
    assert ac.size > 0

    del ac
    # we are not able to check anything here :-(


def test_cleanup():
    """Cleanup."""
    ac = AnyCache()
    cachedir = ac.cachedir

    @ac.anycache()
    def myfunc(posarg, kwarg=3):
        # count the number of calls
        myfunc.callcount += 1
        return posarg + kwarg
    myfunc.callcount = 0

    # first use
    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 1)
    eq_(myfunc(4, 2), 6)
    eq_(myfunc.callcount, 2)
    eq_(myfunc(4, 2), 6)
    eq_(myfunc.callcount, 2)
    assert ac.size > 0

    # clear
    ac.clear()
    eq_(ac.size, 0)
    eq_(tuple(cachedir.glob("*")), tuple())

    # second use
    eq_(myfunc(4, 4), 8)
    eq_(myfunc.callcount, 3)
    assert ac.size > 0

    # clear twice
    ac.clear()
    eq_(ac.size, 0)
    ac.clear()
    eq_(ac.size, 0)


def test_size():
    """Size."""
    ac = AnyCache()

    @ac.anycache()
    def myfunc(posarg, kwarg=3):
        return posarg + kwarg

    eq_(ac.size, 0)
    eq_(len(tuple(ac.cachedir.glob("*.cache"))), 0)
    eq_(myfunc(4, 5), 9)
    eq_(len(tuple(ac.cachedir.glob("*.cache"))), 1)
    size1 = ac.size
    eq_(myfunc(4, 2), 6)
    eq_(ac.size,  2 * size1)
    eq_(len(tuple(ac.cachedir.glob("*.cache"))), 2)


def test_corrupt_cache():
    """Corrupted Cache."""
    cachedir = Path(mkdtemp())
    ac = AnyCache(cachedir=cachedir)

    @ac.anycache()
    def myfunc(posarg, kwarg=3):
        myfunc.callcount += 1
        return posarg + kwarg
    myfunc.callcount = 0

    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 1)
    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 1)

    # corrupt cache
    cachefilepath = list(cachedir.glob("*.cache"))[0]
    with open(str(cachefilepath), "w") as cachefile:
        cachefile.write("foo")

    # repair
    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 2)
    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 2)

    # corrupt dep
    depfilepath = list(cachedir.glob("*.dep"))[0]
    with open(str(depfilepath), "w") as depfile:
        depfile.write("foo")

    # repair
    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 3)
    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 3)

    ac.clear()


def test_cachedir():
    """Corrupted Cache."""
    cachedir = Path(mkdtemp())
    @anycache(cachedir=cachedir)
    def myfunc(posarg, kwarg=3):
        myfunc.callcount += 1
        return posarg + kwarg
    myfunc.callcount = 0

    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 1)
    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 1)

    @anycache(cachedir=cachedir)
    def myfunc(posarg, kwarg=3):
        myfunc.callcount += 1
        return posarg + kwarg
    myfunc.callcount = 0

    eq_(myfunc(4, 5), 9)
    eq_(myfunc.callcount, 0)


def class_test():
    class MyClass(object):

        def __init__(self, posarg, kwarg=3):
            self.posarg = posarg
            self.kwarg = kwarg

        @anycache()
        def func(self, foo):
            return self.posarg + self.kwarg + foo

    a = MyClass(2, 4)
    b = MyClass(1, 3)

    eq_(a.func(6), 12)
    eq_(a.func(6), 12)

    eq_(b.func(6), 10)
    eq_(b.func(6), 10)
    eq_(a.func(6), 12)
