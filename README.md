### SCOOP介绍

Scoop**是一款适用于Windows平台的命令行软件（包）管理工具**。 简单来说，就是可以通过命令行工具（PowerShell、CMD等）实现软件（包）的安装管理等需求，通过简单的一行代码实现软件的下载、安装、卸载、更新等操作。


### scoop基础使用

官网安装说明书： [ScoopInstaller](https://github.com/ScoopInstaller)

1. 先决条件

   - [PowerShell](https://aka.ms/powershell)最新版本或[Windows PowerShell 5.1](https://aka.ms/wmf5download)

2. PowerShell执行策略：

   ```
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. 下载安装脚本,在Powershell中执行以下命令

   ```
   irm get.scoop.sh -outfile 'install.ps1'
   # 国内
   iwr -useb https://gitee.com/glsnames/scoop-installer/raw/master/bin/install.ps1  -outfile 'install.ps1'

   ```

4. 管理员执行安装脚本

   ```
   .\install.ps1 -RunAsAdmin -ScoopDir 'D:\Tools'
   ```

   其中`-RunAsAdmin`是使用管理员角色执行脚本，`-ScoopDir`指定scoop安装目录，软件默认安装在此。

5. 安装该软件仓库中的软件

   确保你已经有 Scoop 环境后，执行以下命令订阅本软件仓库：

   ```powershell
   scoop bucket add sec https://github.com/bright-angel/scoop-bucket
   ```

   执行以下命令安装本仓库中的软件：

   ```powershell
   scoop install sec/<软件名> 
   ```