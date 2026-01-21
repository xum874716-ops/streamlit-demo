"""页面模块"""
from .login import login_page
from .input_page import input_page
from .table_page import table_page
from .model_page import model_page
from .analysis_page import analysis_page
from .ai_page import ai_page

__all__ = [
    'login_page',
    'input_page',
    'table_page',
    'model_page',
    'analysis_page',
    'ai_page'
]