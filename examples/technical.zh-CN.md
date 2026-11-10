# 重试行为

客户端最多可重试 3 次。并非所有失败都可以重试。

设置 `retry_limit=3`，并将超时时间保持为 500 ms。参见[指南](https://example.com/retries)。

```bash
client --retry-limit 3 --timeout-ms 500
```

如果请求失败，显示：“你好，{name}。请重试。”
