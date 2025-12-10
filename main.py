import os
import sys
import io
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, HTMLResponse
from PIL import Image, ImageDraw, ImageFont

# --- 资源配置 ---
IMAGE_FILE = "background.png"
PRIMARY_FONT_FILE = "primary_font.ttf"
FALLBACK_FONT_FILE = "fallback_font.ttf"
FONT_SIZE = 400 

app = FastAPI()

# --- 资源加载和图像处理函数 (适配Web环境) ---

# 在 Serverless 环境中，所有文件都在根目录或指定路径
def resource_path(relative_path):
    # 在标准的 Web/Serverless 环境中，资源文件通常直接位于执行目录
    return os.path.join(os.getcwd(), relative_path) 


def load_font_from_bundle(relative_path, size):
    """从本地资源中加载字体到内存"""
    try:
        abs_path = resource_path(relative_path)
        with open(abs_path, 'rb') as f:
            font_data = io.BytesIO(f.read())
            return ImageFont.truetype(font_data, size)
    except Exception as e:
        print(f"Error loading font: {e}")
        return None

def load_image_from_bundle(relative_path):
    """从本地资源中加载图片到内存"""
    try:
        abs_path = resource_path(relative_path)
        return Image.open(abs_path)
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

def check_text_support(font, text):
    """检查字体是否支持所有字符"""
    if font is None:
        return False
    try:
        # 简化检查，Web 端通常不需要像桌面端那样严格检查字体
        return True 
    except Exception:
        return False

def create_invitation_image(name: str) -> io.BytesIO:
    """根据名字生成邀请函图片数据流"""
    
    # 1. 加载图片
    image = load_image_from_bundle(IMAGE_FILE)
    if image is None:
        raise HTTPException(status_code=500, detail=f"无法加载图片文件: {IMAGE_FILE}")
    draw = ImageDraw.Draw(image)

    # 2. 加载字体
    primary_font = load_font_from_bundle(PRIMARY_FONT_FILE, FONT_SIZE)
    fallback_font = load_font_from_bundle(FALLBACK_FONT_FILE, FONT_SIZE)

    if not primary_font and not fallback_font:
        raise HTTPException(status_code=500, detail="无法加载任何字体文件。")

    font_to_use = primary_font if primary_font else fallback_font
    text = f"致：{name}"

    # 3. 字体检查与选择
    if not primary_font or not check_text_support(primary_font, text):
        font_to_use = fallback_font if fallback_font else ImageFont.load_default()

    # 4. 根据名字长度确定文本位置
    name_len = len(name)
    if name_len == 2:
        position = (2500, 400)
    elif name_len == 3:
        position = (2175, 400)
    elif name_len == 4:
        position = (1700, 400)
    else:
        raise HTTPException(status_code=400, detail="名字长度必须在2到4个字之间！")

    # 5. 添加文本
    draw.text(position, text, font=font_to_use, fill=(255, 255, 255))

    # 6. 将图片保存到内存中的 BytesIO 对象
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


# --- API 路由 ---

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """提供前端页面供用户输入姓名"""
    # 警告：此处的 HTML 仅为演示，实际部署中前端应在 Cloudflare Pages 静态托管
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>经行处邀请函生成器</title>
        <style>
            body {{ font-family: sans-serif; display: flex; flex-direction: column; align-items: center; padding-top: 50px; background-color: #f4f4f9; }}
            .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 350px; text-align: center; }}
            input[type="text"], button {{ padding: 10px; margin: 10px 0; width: 80%; box-sizing: border-box; border-radius: 4px; border: 1px solid #ccc; }}
            button {{ background-color: #007BFF; color: white; border: none; cursor: pointer; transition: background-color 0.3s; }}
            button:hover {{ background-color: #0056b3; }}
            .note {{ font-size: 0.8em; color: #666; margin-top: 20px; white-space: pre-line; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>经行处邀请函生成</h2>
            <p>请输入收件人姓名 (2-4字):</p>
            <input type="text" id="nameInput" placeholder="请输入姓名" maxlength="4">
            <button onclick="generateInvitation()">生成并下载邀请函</button>
            <div id="status"></div>
            <p class="note">
                目前仅支持长度为2-4的姓名，生成需数秒。
                如遇错误欢迎向 student_union@sem.tsinghua.edu.cn 反馈！
            </p>
        </div>
        <script>
            function generateInvitation() {{
                const name = document.getElementById('nameInput').value.trim();
                const statusDiv = document.getElementById('status');
                
                if (name.length < 2 || name.length > 4) {{
                    alert("名字长度必须在2到4个字之间！");
                    return;
                }}

                statusDiv.innerText = "正在生成，请稍候...";
                statusDiv.style.color = 'orange';

                // 调用 API 接口
                fetch(`/api/generate_png/${{name}}`)
                    .then(response => {{
                        if (!response.ok) {{
                            // 如果 HTTP 状态码不是 2xx，则抛出错误
                            return response.json().then(err => {{
                                throw new Error(err.detail || "生成失败");
                            }});
                        }}
                        // 触发浏览器下载
                        return response.blob(); 
                    }})
                    .then(blob => {{
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = `经行处邀请函-${{name}}.png`; 
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        statusDiv.innerText = "生成成功，已开始下载！";
                        statusDiv.style.color = 'green';
                    }})
                    .catch(error => {{
                        statusDiv.innerText = "生成失败: " + error.message;
                        statusDiv.style.color = 'red';
                        console.error('Error:', error);
                    }});
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/generate_png/{name}")
async def generate_png(name: str):
    """
    生成邀请函图片并以 PNG 格式返回。
    """
    try:
        # 1. 核心图像生成逻辑
        img_buffer = create_invitation_image(name)
        
        # 2. 返回 Response
        return Response(content=img_buffer.read(), media_type="image/png")

    except HTTPException:
        # FastAPI  HTTPException 会自动处理，不需要额外捕获
        raise
    except Exception as e:
        print(f"Unhandled error during generation: {e}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

# 本地测试启动命令：uvicorn main:app --reload