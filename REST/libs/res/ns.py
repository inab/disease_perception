#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask_restplus import Namespace, Resource

from .api_models import *

ns = Namespace('cm','Comorbidities network info')
