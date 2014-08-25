import sys

import pytest


pytest_plugins = "pytester"


MOCK_PIPELINE = """
#!/usr/bin/env python

if __name__ == "__main__":

    import os
    import sys

    OUT_DIR = "output_dir"

    if len(sys.argv) > 1:
        sys.exit(1)

    sys.stdout.write("stdout stream\\n")
    sys.stderr.write("stderr stream\\n")

    with open("log.txt", "w") as log:
        log.write("not really\\n")

    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    with open(os.path.join(OUT_DIR, "results.txt"), "w") as result:
        result.write("42\\n")
"""

@pytest.fixture(scope="function")
def mockpipe(request, testdir):
    """Mock pipeline script"""
    mp = testdir.makefile("", pipeline=MOCK_PIPELINE)
    return mp


TEST_OK = """
import os, shutil
from pytest_pipeline import PipelineRun, PipelineTest, mark

class TestMyPipeline(PipelineTest):

    run = PipelineRun(cmd="{python} pipeline")

    @mark.before_run
    def test_and_prep_executable(self):
        shutil.copy2("../pipeline", "pipeline")
        assert os.path.exists("pipeline")

    @mark.after_run
    def test_exit_code(self):
        assert self.run.exit_code == 0
""".format(python=sys.executable)


def test_pipeline_basic(mockpipe, testdir):
    """Test for basic execution order: before_run then after_run"""
    test = testdir.makepyfile(TEST_OK)
    result = testdir.runpytest("-v", test)
    result.stdout.fnmatch_lines([
        "* collected 2 items"
    ])
    expected = [False, False]
    linenos = [0, 0]
    for lineno, line in enumerate(result.outlines, start=1):
        if line.endswith("TestMyPipeline::test_and_prep_executable PASSED"):
            expected[0] = True
            linenos[0] = lineno
        elif line.endswith("TestMyPipeline::test_exit_code PASSED"):
            expected[1] = True
            linenos[1] = lineno
    assert all(expected), "Not all tests in mock pipeline test executed"
    assert linenos[0] < linenos[1], "Mock pipeline test executed in wrong order"


TEST_OK_WITH_NONCLASS = TEST_OK + """

def test_function_standalone():
    assert 1 == 1
"""

def test_pipeline_with_function(mockpipe, testdir):
    """Test for basic execution order with non-class-based test."""
    test = testdir.makepyfile(TEST_OK_WITH_NONCLASS)
    result = testdir.runpytest("-v", test)
    result.stdout.fnmatch_lines([
        "* collected 3 items"
    ])
    expected = [False, False]
    linenos = [0, 0]
    for lineno, line in enumerate(result.outlines, start=1):
        if line.endswith("TestMyPipeline::test_and_prep_executable PASSED"):
            expected[0] = True
            linenos[0] = lineno
        elif line.endswith("TestMyPipeline::test_exit_code PASSED"):
            expected[1] = True
            linenos[1] = lineno
    assert all(expected), "Not all tests in mock pipeline test executed"
    assert linenos[0] < linenos[1], "Mock pipeline test executed in wrong order"


TEST_OK_GRANULAR = """
import os, shutil
from pytest_pipeline import PipelineRun, PipelineTest, mark

class TestMyPipeline(PipelineTest):

    run = PipelineRun(cmd="{python} pipeline")

    @mark.before_run(order=2)
    def test_and_prep_executable(self):
        shutil.copy2("../pipeline", "pipeline")
        assert os.path.exists("pipeline")

    @mark.before_run(order=1)
    def test_init_condition(self):
        assert not os.path.exists("pipeline")

    @mark.after_run(order=1)
    def test_exit_code(self):
        assert self.run.exit_code == 0

    @mark.after_run(order=2)
    def test_output_file(self):
        assert os.path.exists(os.path.join("output_dir", "results.txt"))
""".format(python=sys.executable)


def test_pipeline_granular(mockpipe, testdir):
    """Test for execution with 'order' specified in before_run and after_run"""
    test = testdir.makepyfile(TEST_OK_GRANULAR)
    result = testdir.runpytest("-v", test)
    result.stdout.fnmatch_lines([
        "* collected 4 items"
    ])
    expected = [False, False, False, False]
    linenos = [0, 0, 0, 0]
    for lineno, line in enumerate(result.outlines, start=1):
        if line.endswith("TestMyPipeline::test_init_condition PASSED"):
            expected[0] = True
            linenos[0] = lineno
        elif line.endswith("TestMyPipeline::test_and_prep_executable PASSED"):
            expected[1] = True
            linenos[1] = lineno
        elif line.endswith("TestMyPipeline::test_exit_code PASSED"):
            expected[2] = True
            linenos[2] = lineno
        elif line.endswith("TestMyPipeline::test_output_file PASSED"):
            expected[3] = True
            linenos[3] = lineno
    assert all(expected), "Not all tests in mock pipeline test executed"
    assert linenos == sorted(linenos), "Mock pipeline test executed in wrong order"


TEST_NO_ORDER_NON_TEST = """
import os, shutil
from pytest_pipeline import PipelineRun, PipelineTest, mark

class TestMyPipeline(PipelineTest):

    run = PipelineRun(cmd="{python} pipeline")

    @mark.before_run(order=2)
    def prep_executable(self):
        shutil.copy2("../pipeline", "pipeline")

    @mark.after_run
    def test_exit_code(self):
        assert self.run.exit_code == 0
"""

def test_pipeline_no_order_non_test(mockpipe, testdir):
    test = testdir.makepyfile(TEST_NO_ORDER_NON_TEST)
    result = testdir.runpytest("-v", test)
    result.stdout.fnmatch_lines([
        "* collected 0 items / 1 errors"
    ])
    result.stdout.fnmatch_lines([
        "*ValueError: Can not decorate non-test functions with 'order'"
    ])


MOCK_PIPELINE_TIMEOUT = """
#!/usr/bin/env python

if __name__ == "__main__":

    import time
    time.sleep(10)
"""


TEST_TIMEOUT = """
import os, shutil
from pytest_pipeline import PipelineRun, PipelineTest, mark

class TestMyPipeline(PipelineTest):

    run = PipelineRun(cmd="{python} pipeline", timeout=0.1)

    @mark.before_run
    def test_and_prep_executable(self):
        shutil.copy2("../pipeline", "pipeline")
        assert os.path.exists("pipeline")

    @mark.after_run
    def test_exit_code(self):
        assert self.run.exit_code != 0
""".format(python=sys.executable)


@pytest.fixture(scope="function")
def mockpipe_timeout(request, testdir):
    """Mock pipeline script with timeout"""
    mp = testdir.makefile("", pipeline=MOCK_PIPELINE_TIMEOUT)
    return mp


def test_pipeline_timeout(mockpipe_timeout, testdir):
    """Test for execution with timeout"""
    test = testdir.makepyfile(TEST_TIMEOUT)
    result = testdir.runpytest("-v", test)
    result.stdout.fnmatch_lines([
        "* collected 2 items",
        "*Failed: Process is taking longer than 0.1 seconds",
    ])
