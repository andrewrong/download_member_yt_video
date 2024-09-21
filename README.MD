# YouTube Cookie 下载器

这是一个使用Python编写的工具,用于从Chrome浏览器中提取YouTube的cookies,并使用这些cookies下载YouTube视频。

## 功能

- 从Chrome浏览器中提取YouTube相关的cookies
- 将提取的cookies保存为Netscape格式的文件
- 使用保存的cookies下载YouTube视频
- 会自动的保存最新的cookies然后来下载，手动下载会guo q

## 依赖

- browser_cookie3
- yt-dlp

## 使用方法

1. 确保已安装所有依赖项。

2. 在`main.py`中,修改`profile_path`变量以匹配你的Chrome用户数据目录:

3. 在`urls.txt`文件中添加要下载的YouTube视频URL,每行一个。

4. 运行脚本:

## 注意事项

- 此脚本仅适用于Chrome浏览器。
- 确保在运行脚本之前已登录YouTube。
- 下载的视频将保存在脚本所在的目录中。

## 许可

本项目采用 GNU Lesser General Public License v3.0 (LGPL-3.0) 许可证。这意味着您可以自由地使用、修改和分发本软件，但是如果您修改了本软件，您必须以相同的许可证发布修改后的版本。详细信息请参阅相关文件。
