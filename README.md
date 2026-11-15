# WindTerm Windows SSH 补丁

修复 WindTerm 读取 Windows 登录名失败导致的 SSH 连接问题。已在 WindTerm 2.7.0 Windows x86-64 便携版验证。

## 准备原始 DLL

下载并解压 `WindTerm_2.7.0_Windows_Portable_x86_64.zip`。[WindTerm 2.7.0 官方发布页](https://github.com/kingToolbox/WindTerm/releases/tag/2.7.0)

在解压后的 WindTerm 目录打开 PowerShell，查看 `ssh.dll` 的 SHA-256。

```powershell
(Get-FileHash -Algorithm SHA256 -LiteralPath .\ssh.dll).Hash
```

2.7.0 Windows x86-64 便携版的原始 `ssh.dll` 哈希为 `1308CE9CC94CBB902E1A8E3A31E10B278E9B12201D938C0A87719B91E6542A09`。

## 生成并安装补丁

确认哈希一致后，在本仓库目录打开 PowerShell。将 `$sshDll` 改成解压后的 `ssh.dll` 路径，用 Python 3 运行以下命令。

```powershell
$sshDll = 'C:\Apps\WindTerm_2.7.0\ssh.dll'
python .\patch_ssh.py --input $sshDll --output .\ssh-generated.dll
```

生成成功后，完全退出 WindTerm。在同一个 PowerShell 窗口运行以下命令，再启动 WindTerm 验证 SSH 登录。

```powershell
Copy-Item -LiteralPath .\ssh-generated.dll -Destination $sshDll -Force
```

换版本时，把 `$sshDll` 改成对应版本的路径。脚本在代码段里唯一匹配到目标机器码时才会生成 DLL。

## 修复内容

原排查中，`GetUserNameA` 首次查询给出的缓冲区大小是 14 字节，实际读取登录名需要 15 字节。补丁跳过长度查询，直接使用 4096 字节缓冲区，并重算 PE 校验和。
