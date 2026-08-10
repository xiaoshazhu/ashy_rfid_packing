# 桌面二维码扫描设备

#### 介绍
{**以下是 Gitee 平台说明，您可以替换此简介**
Gitee 是 OSCHINA 推出的基于 Git 的代码托管平台（同时支持 SVN）。专为开发者提供稳定、高效、安全的云端软件开发协作平台
无论是个人、团队、或是企业，都能够用 Gitee 实现代码托管、项目管理、协作开发。企业项目请看 [https://gitee.com/enterprises](https://gitee.com/enterprises)}

#### 软件架构
软件架构说明
    

#### 安装教程

1.  在命令提示符或终端中运行以下命令来启动 GUI 界面 auto-py-to-exe
2.  安装
3. 配置环境变量 pip show auto-py-to-exe C:\Users\14917\AppData\Roaming\Python\Python312\Scripts
4. 重启电脑
5. pyinstaller --noconfirm --onedir --windowed --icon "C:\Users\14917\Downloads\logo.ico" --name "装箱扫码" --hide-console "hide-early" --uac-admin  "C:\Users\14917\PycharmProjects\Desktop_QR_Send\main.py"

#### 使用说明

pip install PySide6 pyserial pyzbar opencv-python Pillow code128 numpy pywin32 websockets pygame python-barcode

#### 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request


#### 特技

1.  使用 Readme\_XXX.md 来支持不同的语言，例如 Readme\_en.md, Readme\_zh.md
2.  Gitee 官方博客 [blog.gitee.com](https://blog.gitee.com)
3.  你可以 [https://gitee.com/explore](https://gitee.com/explore) 这个地址来了解 Gitee 上的优秀开源项目
4.  [GVP](https://gitee.com/gvp) 全称是 Gitee 最有价值开源项目，是综合评定出的优秀开源项目
5.  Gitee 官方提供的使用手册 [https://gitee.com/help](https://gitee.com/help)
6.  Gitee 封面人物是一档用来展示 Gitee 会员风采的栏目 [https://gitee.com/gitee-stars/](https://gitee.com/gitee-stars/)

AI对话前提

请你称呼我为：“小屿”，并在后续回答用中文回答我。
1.分析我当前的项目，后续修改在我的项目上修改，前提保证业务跑通，代码逻辑正常，没有明确要求，不要制造假数据，假页面。
2.你有修改的篇幅大要求多，就先列一个修改计划，我审核后再允许修改。
3.你后续修改要把修改了哪些文件告诉我，文件在项目的什么位置。
4.有什么自己添加的数据，要明确出处，网址获取的数据，要进行二次反向验证才使用。
5.没有明确指令，不要上传和修改我的GitHub代码，Gitee代码。
6.如果生成什么图片视频，要告诉我相应存放的位置。
7.每一次新项目，要先分析整个项目干什么。
8.后续项目整体流程跑通，需要你写功能文档、开发文档。
9.关于我俩对话久了，你要适时压缩上下文，还要自己解决乱码问题。
10.这些是后续你修改代码，操作文件的前提，明白吗？