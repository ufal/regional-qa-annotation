### Service Installation

To install the service, put this file in ``/etc/systemd/system/``.

The service loads the MT API key as the systemd credential `mt-llm-key` from
`/etc/regional-qa/mt-llm-key`. **Without that file the service does not
start**, so create it first, readable by root only:

```sh
sudo install -d -m 700 /etc/regional-qa
sudo install -m 600 /dev/stdin /etc/regional-qa/mt-llm-key   # paste the key, then Ctrl-D
```

`MT_LANGS` in the unit lists the languages that get the MT button.

After changing the unit or the key, reload and restart, and check the status:
`systemctl start` does not report a failure.

```sh
sudo systemctl daemon-reload
sudo systemctl restart regional-qa && systemctl status regional-qa
```
