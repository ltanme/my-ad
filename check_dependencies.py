#!/usr/bin/env python3
"""检查项目依赖是否正确安装"""
import sys

def check_module(name, import_name=None, min_version=None):
    """检查模块是否安装"""
    if import_name is None:
        import_name = name.lower().replace('-', '_')
    
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        
        if min_version and version != 'unknown':
            from packaging import version as pkg_version
            if pkg_version.parse(version) < pkg_version.parse(min_version):
                print(f"⚠️  {name} - 版本过低 (当前: {version}, 需要: >={min_version})")
                return False
        
        print(f"✓ {name} - {version}")
        return True
    except ImportError:
        print(f"✗ {name} - 未安装")
        return False
    except Exception as e:
        print(f"⚠️  {name} - 检查失败: {e}")
        return False


print("=" * 60)
print("检查项目依赖")
print("=" * 60)

print("\n[核心依赖]")
all_ok = True
all_ok &= check_module("PyQt5", min_version="5.15.0")
all_ok &= check_module("PyYAML", "yaml", min_version="5.4.0")

print("\n[Admin 模块依赖]")
all_ok &= check_module("Flask", "flask", min_version="2.3.0")
all_ok &= check_module("Werkzeug", "werkzeug", min_version="2.3.0")

print("\n[可选依赖]")
check_module("Pillow", "PIL")
check_module("piexif")
check_module("python-vlc", "vlc")

print("\n" + "=" * 60)
if all_ok:
    print("✓ 所有核心依赖已正确安装")
    print("\n可以运行:")
    print("  - Viewer: python viewer/main.py")
    print("  - Admin:  python admin/app.py")
else:
    print("✗ 部分核心依赖未安装或版本不符")
    print("\n请运行: pip install -r requirements.txt")
    sys.exit(1)

print("=" * 60)
