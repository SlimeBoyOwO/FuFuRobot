# FUFURobot

## 项目概括

本项目使用了大模型Deepseek API接口，实现了一个基于Python的聊天机器人

由于deepseek有思考模式，因此我增加了深入思考的模式。

由于课设任务，我加入了数据库操作模式。

## 使用方法

本项目内部已经将记忆系统和人设设计好了。

支持修改，不过要使用本项目，需要先注册[deepseek API](https://platform.deepseek.com/usage)，获取API Key。

下面给出修改方法：

#### 修改API

进入backend文件夹，添加.env文件 .env文件格式如下：

DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxx

DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions

DEEPSEEK_MODEL=deepseek-chat

DB_NAME=students.db

BACKEND_HOST=127.0.0.1

BACKEND_PORT=8000

FRONTEND_HOST=127.0.0.1

FRONTEND_PORT=8080

修改 第一行内容，为自己的Deepseek API Key即可。

(目前项目只支持Deepseek API，其他API接口暂时不支持，见谅)

#### 修改人设

进入backend文件夹，找到config.py文件，修改# AI性格设定 (System Prompt)以下内容。

#### 修改记忆系统

记忆系统分为四层缓存

修改deepseek单次硬对话大小，在backend文件夹下的llm文件夹，找到chat_mode.py文件，修改Tough_Memory即可，默认80条。

修改事实记忆，用户动态记忆，ai状态记忆和保存的上下文，在backend文件夹下的llm文件夹，找到memory_manager.py文件，

其第10行修改fact_num, lastly_num, aistate_num, savedcontext_num即可，上面已有默认数字。

## 启动方式

根据uv使用指南文档,建议使用uv来管理环境变量

或者直接下载requirements.txt文件的库，使用pip install -r requirements.txt安装依赖

然后在资源管理器里双击start.bat即可启动

## 声明

本项目仅供学习交流使用，禁止用于商业用途。

用到的部分图像，如有侵权，请联系删除。