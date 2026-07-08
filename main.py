"""月薪喵桌面宠物 - 程序入口"""

import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import PetApp


def main():
    """启动月薪喵桌宠应用。"""
    app = PetApp(sys.argv)
    sys.exit(app.run())


if __name__ == '__main__':
    main()
