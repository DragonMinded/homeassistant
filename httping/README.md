Utility for monitoring a local or remote IP for binary sensors in Home Assistant, since the functionality was taken out.

Run it similar to:

```
python3 ping.py --host 10.0.0.1 --port 34567 --timeout 1.0 --count 2
```

The above command will ping 10.0.0.1 once a second with a timeout of 1.0 seconds before considering a ping lost, and will mark the host down after 2 consecutive ping failures. After a successful ping response, it will mark the host up. If you don't care about timeouts or failure counts, you can instead run the simpler command below which will accomplish a similar task.

```
python3 ping.py --host 10.0.0.1 --port 34567
```

The above command will ping 10.0.0.1 once a second with a 0.5 second timeout before considering a ping lost. There is no count of failure. If a ping fails to come back, the host is marked down. If a ping comes back, the host is marked up.

Both commands host a simple REST server on localhost:34567 that response with some JSON that looks like the following:

```
{"state": "up", "host": "10.0.0.1"}
```

If the host is marked up, the state will be `up`. If the host is marked down, the state will be `down`. You can hit this endpoint as often or little as you want, and the most recent host status will be returned as JSON.

To use this as a binary sensor, add something similar to the following to your `configuration.yaml` file:

```
binary_sensor:
 - platform: rest
   name: 'Router Status'
   resource: http://127.0.0.1:34567/
   method: GET
   device_class: connectivity
   value_template: '{{ value_json.state == "up" }}'
   timeout: 1
   scan_interval: 1
```

This will instruct Home Assistant to poll the endpoint once a second, with a one second timeout. If the host was marked up, the "Router Status" binary sensor will be marked as "connected". If it was marked down, the "Router Status" binary sensor will be marked as "disconnected". You can run multiple scripts to monitor multiple hosts. Just make sure to put them on different ports and to reference the correct port in your binary sensors. Also it goes without saying but don't be an idiot and point this at a box you don't own or shouldn't be pinging for connectivity checks.
