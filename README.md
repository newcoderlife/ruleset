# chndomains

这个项目用于生成 RouterOS DNS forwarder 规则，把不同域名转发到不同的上游 DNS。

典型用途是：

- 国内域名走国内 DNS，例如 `223.5.5.5`、`114.114.114.114`
- 非国内域名走海外 DNS，例如 `1.1.1.1`、`8.8.8.8`
- 在 RouterOS 上通过 `/ip/dns/static type=FWD` 实现按域名分流

生成后的 RouterOS 脚本是 `chndomains.rsc`，发布在 GitHub Releases 的 `latest` 里。

## 生成规则

```sh
make generate
```

检查生成器和输出是否稳定：

```sh
make check
```

默认上游 DNS：

- `cn`: `223.5.5.5,114.114.114.114`
- `noncn`: `1.1.1.1,8.8.8.8`

如果要自定义上游 DNS：

```sh
python3 generate.py --cn-dns 223.5.5.5,114.114.114.114 --noncn-dns 1.1.1.1,8.8.8.8
```

## 发布产物

`master` 分支更新后，GitHub Actions 会生成 `chndomains.rsc`，并覆盖发布到固定的 `latest` release。也可以在 GitHub Actions 里手动触发发布。

## 在 RouterOS 上使用

在 RouterOS 里创建更新脚本：

```routeros
/system script add name=ruleset-update source={
    /tool fetch url="https://github.com/newcoderlife/chndomains/releases/latest/download/chndomains.rsc" dst-path=chndomains.rsc mode=https
    /import file-name=chndomains.rsc
}
```

手动执行一次：

```routeros
/system script run ruleset-update
```

每天 04:00 自动更新：

```routeros
/system scheduler add name=ruleset-update interval=1d start-time=04:00:00 on-event=ruleset-update
```

## 规则文件

- `cn`：国内域名入口文件。
- `noncn`：非国内域名入口文件。
- `ruleset.cn`：共享的国内域名 include 列表。
- `ruleset.noncn`：共享的非国内域名 include 列表。
- `domains/`：按服务或公司拆分的域名列表。
- `local.cn`：本地自定义国内域名，可选。
- `local.noncn`：本地自定义非国内域名，可选。

域名条目需要带结尾的点，例如：

```txt
twitter.com.
```

include 写法：

```txt
include:domains/github
```

## 添加域名

优先把域名放到已有的公司或服务文件里，例如：

- GitHub Copilot 相关域名放到 `domains/github`
- xAI/Grok 相关域名放到 `domains/twitter`
- OpenAI 相关域名放到 `domains/openai`

如果没有合适的已有文件，可以在 `domains/` 下新建文件，再把它 include 到 `ruleset.cn` 或 `ruleset.noncn`。

修改后运行：

```sh
make check
```

## 参考项目

- [felixonmars/dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list)：面向 DNS 服务的中国域名列表。
- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)：社区维护的域名列表，用于生成 `geosite.dat`。
- [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat)：增强版路由规则数据，适用于 V2Ray、Xray、mihomo、sing-box 等客户端。
