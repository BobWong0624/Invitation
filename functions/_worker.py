# cloudflare-pages-functions/_worker.py
from main import app
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

# Cloudflare Pages Functions 使用 Werkzeug 包装器来运行 Python ASGI 应用。
# 我们需要确保 FastAPI 的响应能被正确处理。

# 导出 FastAPI 应用
# Cloudflare Pages Functions 会找到这个变量并作为入口
# 它会自动处理ASGI请求/响应循环。

# 如果您想直接在 pages-functions 中处理，通常只需要导入 app
# 但为了确保兼容性，我们使用一个简单的函数来包装它（尽管 Pages 文档通常只要求导入 app）
# 推荐做法是直接导出 app:
# from main import app as application # 有些环境习惯用 application
# 
# 考虑到 Pages Functions 的特殊性，最简单的方式是直接导出您的 FastAPI app 实例:
application = app