# OKX-bitget-copytrading
复制你在OKX的跟单仓位并且节省返佣
这是一个开源的okx跟单复制软件，目前尚未测试，⚠⚠⚠不要把他复制到生产环境中来⚠⚠⚠
---
由于okx的api限制，目前已经无法正常实时获取到跟单员的仓位，所以现在需要这些内容来实现复制
---
![](https://i0.hdslb.com/bfs/article/727bdd3333f20f9cea265fc9d7260ae1498348349.png)
⚠⚠⚠⚠请合理使用，不要用于带单，破坏平衡⚠⚠⚠⚠
---
Bitget交易所有超高的返佣，是一个有较大声望的交易所，使用[我的返佣(点击我注册)](https://partner.bitget.fit/bg/WJ9TDV)，可以省更多佣金，还可以激励我的开发！
---
你也可以使用我的[okx邀请码](https://okx.com/join/46420261)，它没有返佣，但是对我也有帮助！
---
当然这不是必需的，我没有在程序中增加任何判断的限制，就算不用也可以
---

需要什么

1.需要一个可以跟单的okx账户，跟单你想跟单的交易员，这意味着，如果交易员满人，你就不能再跟单了

2.一个bitget账户，用于下单

3.两个账户有一定资金，okx存放少量资金用于跟单，两个账户开通api，并且保存好api-key，密钥，不要泄露给任何人！！！

4.稳定的网络环境，如VPN或购买日本地区服务器

5.Python环境是必须的，可以百度搜索

6.安装requests库，安装python后，使用pip install requests安装这个库 

7.填入所需密钥信息，启动

原理：利用okx api读取跟单带单员的数据，并自动获取两个账户的余额，自动计算比例，下单，平仓，减仓增仓
---
