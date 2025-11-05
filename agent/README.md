3. build image
```shell
docker build -t crpi-wixjy6gci86ms14e.cn-hongkong.personal.cr.aliyuncs.com/ay-dev/basic-agent-app:latest .
```


kubectl -n application  create secret generic basic-agent-secrets \
  --from-literal=tongyi_api_key='sk-f0029ee74a454bddbe1a79c2d55aaca3' \
  --from-literal=serpapi_api_key='d8424631bd0e00b82aa9aab04a4dedb496104f6b19d3157ada61178c94047fb6' \
  --from-literal=travily_api_key='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'
