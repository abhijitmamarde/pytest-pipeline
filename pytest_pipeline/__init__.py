# -*- coding: utf-8 -*-
"""
    pytest_pipeline
    ~~~~~~~~~~~~~~~

    Pytest plugin for functional testing of data analysis pipelines.

    :license: BSD

"""
# (c) 2014-2020 Wibowo Arindrarto <bow@bow.web.id>

RELEASE = False

__version_info__ = ("0", "4", "0")
__version__ = ".".join(__version_info__)
__version__ += "-dev" if not RELEASE else ""

__author__ = "Wibowo Arindrarto"
__contact__ = "bow@bow.web.id"
__homepage__ = "https://github.com/bow/pytest-pipeline"

# so we can keep the info above for setup.py
try:
    from .core import PipelineRun  # noqa
except ImportError:
    pass
