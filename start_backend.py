import subprocess
import time

# 启动后端服务器
print("Starting backend server...")
# 使用虚拟环境中的Python解释器
python_path = r"D:\delvelop_project\ai_project\diskbench_pro\.venv_new\Scripts\python.exe"
backend_process = subprocess.Popen(
    [python_path, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"],
    cwd=r"D:\delvelop_project\ai_project\diskbench_pro\backend"
)

# 保持脚本运行，防止后端服务器被终止
print("Backend server started. Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping backend server...")
    backend_process.terminate()
    backend_process.wait()
    print("Backend server stopped.")