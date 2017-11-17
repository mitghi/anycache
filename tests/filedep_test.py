from time import sleep
from pathlib import Path
from tempfile import NamedTemporaryFile
from nose.tools import eq_

from anycache import anycache


def test_filedepfunc():
    """F."""

    with NamedTemporaryFile("w") as depfile1:
        with NamedTemporaryFile("w") as depfile2:
            depfile1.write("dep1")
            depfile2.write("dep2")
            depfilepath1 = Path(depfile1.name)
            depfilepath2 = Path(depfile2.name)

            def depfilefunc(result, posarg, kwarg=3):
                deps = [depfilepath1]
                if posarg == 4:
                    deps.append(depfile2.name)
                return deps

            @anycache(debug=True, depfilefunc=depfilefunc)
            def myfunc(posarg, kwarg=3):
                # count the number of calls
                myfunc.callcount += 1
                return posarg + kwarg
            myfunc.callcount = 0

            eq_(myfunc(4, 5), 9)
            eq_(myfunc.callcount, 1)
            eq_(myfunc(1, 5), 6)
            eq_(myfunc.callcount, 2)
            eq_(myfunc(4, 5), 9)
            eq_(myfunc.callcount, 2)

            sleep(2)
            depfilepath1.touch()

            eq_(myfunc(4, 5), 9)
            eq_(myfunc.callcount, 3)
            eq_(myfunc(1, 5), 6)
            eq_(myfunc.callcount, 4)

            eq_(myfunc(4, 5), 9)
            eq_(myfunc.callcount, 4)
            eq_(myfunc(1, 5), 6)
            eq_(myfunc.callcount, 4)

            sleep(2)
            depfilepath2.touch()
            eq_(myfunc(4, 5), 9)
            eq_(myfunc.callcount, 5)
            eq_(myfunc(1, 5), 6)
            eq_(myfunc.callcount, 5)

            # We are touching the source code of 'myfunc'
            sleep(2)
            Path(__file__).touch()
            eq_(myfunc(4, 5), 9)
            eq_(myfunc.callcount, 6)
            eq_(myfunc(1, 5), 6)
            eq_(myfunc.callcount, 7)
