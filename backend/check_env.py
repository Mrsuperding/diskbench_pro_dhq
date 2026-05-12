import sys
import os

print("Python解释器路径:", sys.executable)
print("Python版本:", sys.version)
print("\n已安装的包:")
try:
    import pkg_resources
    for pkg in pkg_resources.working_set:
        print(f"{pkg.key}=={pkg.version}")
except ImportError:
    print("无法导入pkg_resources模块")

print("\n当前工作目录:", os.getcwd())