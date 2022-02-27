# hax_renew

> 纯萌新, 写的不好请见谅

## 使用服务介绍

对于 reCaptha, 使用到了腾讯云提供的免费[语音识别 ASR](https://cloud.tencent.com/product/asr), 用到其每月提供 10 小时的录音文件识别

相关参考文章

- [Python破解Google验证码ReCaptchav3的成功案例(附代码)(免费)(2022) - 二叉树的博客 (spiritysdx.top)](https://www.spiritysdx.top/59/)

对于 续期界面的 图片验证码, 使用到了 [TrueCaptcha](https://apitruecaptcha.org/) 的服务, 参考了同一个作者的文章

- [免费破解图片验证码(数字或中英混合)(附代码)(2022) - 二叉树的博客 (spiritysdx.top)](https://www.spiritysdx.top/61/)

模拟浏览器操作使用了 microsoft 的 [playwright](https://github.com/microsoft/playwright), 录制操作, 大大节省了初步开发工作量

用到了 [cf_clearance](https://github.com/vvanglro/cf_clearance) , 用以处理可能的 cloudflare 五秒盾, 当然, 一般出了五秒盾 reCaptchav3 八成也过不了

## 开始使用

### ASR api key 获取

> 可参考上述文章

0. 注册账号

1. 在 [访问密钥 - 控制台 (tencent.com)](https://console.cloud.tencent.com/cam/capi), 生成访问密钥对, 为了安全, 根据提示创建一个子账号

   创建完的用户大致长这样

   ![image-20220227224843788](https://s2.loli.net/2022/02/27/aOYkhmjy3teNHqw.png)

2. 在 [用户 - 控制台 (tencent.com)](https://console.cloud.tencent.com/cam) 页面可以看见子用户, 如第一步操作不太清楚, 可以在此页面添加用户, **操作-授权** 下也可以补充子用户的用户权限 (必须有 QcloudASRFullAccess 存在) 

3. 点击进入 子用户, 找到`API 密钥`一项

   ![image-20220227230140369](https://s2.loli.net/2022/02/27/tJjglOX3Ln26K1V.png)

   保存 SecretId 与 SecretKey 备用

### TrueCaptcha api key 获取

注册账号后直接从 [https://apitruecaptcha.org/api](https://apitruecaptcha.org/api) 拿到 userid 和 apikey 备用	

### 脚本使用

#### 在本地或个人服务器上使用

1. **安装依赖**

   ```shell
   python3 -m pip install --upgrade pip
   python3 -m pip install -r requirements.txt
   python3 -m playwright install # playwright install also works
   ```

   其中 `playwright install`时会下载多个浏览器内核, 比较依赖网络

2. **完善变量**

   | 环境变量           | 含义                              |
   | ------------------ | --------------------------------- |
   | TRUECAPTCHA_USERID | TrueCaptcha 的 userid             |
   | TRUECAPTCHA_APIKEY | TrueCaptcha 的 apikey             |
   | SECRETID           | 腾讯云 SECRETID                   |
   | SECRETKEY          | 腾讯云 SECRETKEY                  |
   | USRNAME            | hax 登陆时填写的用户名            |
   | PASSWORD           | hax 登陆时填写的密码              |
   | DRIVER             | [弃用] selenium chromedriver 路径 |
   | UA                 | 浏览器使用的 UA                   |

   这些值未定义时将使用 demo.py 内预设定的值, 因此也可直接修改 demo.py 文件内相应字段

3. **脚本运行**

   默认运行在 headless 模式, 有需要可自行修改

   ```shell
   python3 demo.py
   ```

#### 托管到 Github Action

coming soon

## 运行生成文件说明

脚本运行需要当前目录的写权限, 其会创建 captcha.png 与 state.json 两个文件

captcha.png 为处理 数字验证码的中间文件, state.json 储存了 cookies, 避免重复登录
