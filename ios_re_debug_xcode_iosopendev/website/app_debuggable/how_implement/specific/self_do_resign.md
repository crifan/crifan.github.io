# 手动给单个二进制文件重签名

后来发现另外方式也暂时可以实现：任意进程可调试

对于要调试的文件：

* 服务进程=二进制文件
  * 比如
    * `AuthKit`的daemon服务进程的二进制文件：`akd`
* app内的核心二进制文件
  * 比如
    * iOS系统内置app：`设置`=`Preferences`的 `Preferences.app/Preferences`
