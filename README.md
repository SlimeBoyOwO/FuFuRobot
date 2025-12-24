<div style="text-align: center; padding: 40px 0; min-height: 200px;">
  <span style="color:#1E90FF;text-shadow: 0 0 10px rgba(30,144,255,0.5); font-size: 2.5rem;">
    FUFURobot
  </span>
  <p style="margin-top: 20px; color: #666;">✨ 𝓕𝓾𝓯𝓾 𝓲𝓼 𝓼𝓸 𝓬𝓾𝓽𝓮! ✨</p>
  <p style="color: #888;">🌟 **芙·芙·可·爱·捏！** 🌙.</p>
</div>


![FUFU](./ShowImages/title.png)


***
## 项目概括
<span style="background: linear-gradient(90deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #fee140 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
✨FUFURobot是一个基于Deepseek API的聊天机器人，具有记忆系统、人设设定和自定义API接口等功能✨。
</span>

***
## 项目模式

- 聊天模式
- 专注模型
- 数据库模式

***
## 使用方法

本项目内部已经将记忆系统和人设设计好了。

支持修改，不过要使用本项目，需要先注册[deepseek API](https://platform.deepseek.com/usage)，获取API Key。

下面给出修改方法：

***
#### 修改API

进入backend文件夹，添加.env文件 .env文件格式如下：

```bash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_MODEL=deepseek-chat
DB_NAME=students.db
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=8080
```

修改 第一行内容，为自己的Deepseek API Key即可。

(目前项目只支持Deepseek API，其他API接口暂时不支持，见谅)

***
#### 修改人设

进入backend文件夹，找到config.py文件，修改# AI性格设定 (System Prompt)以下内容。

***
#### 修改记忆系统

记忆系统分为**四层缓存**

修改deepseek单次硬对话大小，在backend文件夹下的llm文件夹，找到**chat_mode.py**文件，修改Tough_Memory即可，默认80条。

修改**事实记忆**，**用户动态记忆**，**ai状态记忆和保存的上下文**，在backend文件夹下的llm文件夹，找到**memory_manager.py**文件，

其第10行修改fact_num, lastly_num, aistate_num, savedcontext_num即可，上面已有默认数字。

***
## 启动方式

根据uv使用指南文档,建议使用uv来管理环境变量

或者直接下载requirements.txt文件的库，使用pip install -r requirements.txt安装依赖

然后在资源管理器里双击start.bat即可启动

***
## 声明

本项目仅供学习交流使用，禁止用于商业用途。

用到的部分图像，如有侵权，请联系删除。

邮箱：1459134925@qq.com

![Call me](./ShowImages/end.png)
