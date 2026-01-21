"""配置文件 - 存放全局配置和常量"""
import os

# 用户数据库
USERS = {
    "admin": {"password": "admin123", "role": "管理员"},
    "user1": {"password": "user123", "role": "普通用户"},
    "manager": {"password": "manager123", "role": "经理"}
}

# 资源能力组配置（名称 -> CSV文件路径）
RESOURCE_GROUPS = {
    "五轴加工中心1组": "五轴加工中心一组.csv",
    "钳工组": "钳工组.csv",
}

# DeepSeek API配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "your-api-key-here")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 页面配置
PAGE_CONFIG = {
    "page_title":  "产能测算系统",
    "page_icon": "🏭",
    "layout":  "wide"
}

# 页面列表和图标
PAGES = ["产能数据表", "数据输入", "产能模型", "产能分析", "AI分析"]

PAGE_ICONS = {
    "产能数据表": "📊",
    "数据输入": "📝",
    "产能模型": "🔧",
    "产能分析": "📈",
    "AI分析": "🤖"
}