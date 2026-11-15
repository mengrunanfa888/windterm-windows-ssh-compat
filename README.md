# WindTerm Windows SSH 补丁

修复 WindTerm 读取 Windows 登录名失败导致的 SSH 连接问题。已在 WindTerm 2.7.0 Windows x86-64 便携版验证。

## 使用现成补丁

随附的 `ssh-patched.dll` 适用于 **WindTerm 2.7.0 Windows x86-64 便携版**。[WindTerm 2.7.0 官方发布页](https://github.com/kingToolbox/WindTerm/releases/tag/2.7.0)

在 WindTerm 安装目录打开 PowerShell，运行以下命令查看当前 `ssh.dll` 的 SHA-256。

```powershell
(Get-FileHash -Algorithm SHA256 -LiteralPath .\ssh.dll).Hash
```

原始 `ssh.dll` 的 SHA-256 为 `1308CE9CC94CBB902E1A8E3A31E10B278E9B12201D938C0A87719B91E6542A09`。

哈希一致后，完全退出 WindTerm。

用 `ssh-patched.dll` 替换原目录的 `ssh.dll` , 替换后启动 WindTerm。

## 生成补丁

在本目录用 Python 3 运行以下命令。

```powershell
python .\patch_ssh.py --input .\ssh-original.dll --output .\ssh-generated.dll
```

换版本时，把 `--input` 改成该版本的 `ssh.dll` 路径。脚本在代码段里唯一匹配到目标机器码时才会生成 DLL。

退出 WindTerm 后，用生成的文件替换对应版本安装目录里的 `ssh.dll`，再进行手动验证 SSH 登录。

## 修复内容

原排查中，`GetUserNameA` 首次查询给出的缓冲区大小是 14 字节，实际读取登录名需要 15 字节。补丁跳过长度查询，直接使用 4096 字节缓冲区，并重算 PE 校验和。
