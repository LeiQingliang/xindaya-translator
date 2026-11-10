# Retry behavior

The client may retry up to 3 times. Not all failures are retryable.

Set `retry_limit=3` and keep the timeout at 500 ms. See [the guide](https://example.com/retries).

```bash
client --retry-limit 3 --timeout-ms 500
```

If the request fails, display: "Hello, {name}. Please try again."
