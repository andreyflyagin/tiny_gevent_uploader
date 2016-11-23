# tiny_gevent_uploader
Tiny gevent web server based on Flask with websocket progress bar. It can upload large files and perform async fake processing just for load.

## Installation & Run
tested on ubuntu 14.04

```
sudo apt-get install python-dev libssl-dev libpcre3 libpcre3-dev build-essential python-pip git
pip install Flask Flask-uWSGI-WebSocket gevent

cd
git clone https://github.com/andreyflyagin/tiny_gevent_uploader.git

cd tiny_gevent_uploader
export TGU_ADDR=192.168.88.140:5000 TGU_UPLOAD="/tmp" ; uwsgi --master --http :5000 --http-websockets --wsgi tiny_gevent_uploader.app:application --gevent 80
```

Open 192.168.88.140:5000 with you browser, where 192.168.88.140 is your host.
You can share unique processing url to watch progress in different tabs.
Try to upload some 5-10GB files, have fun.


## Future
- [ ] Sharing upload progress by the same url.
- [ ] Write tests.
- [ ] Wrap into the shell command like SimpleHTTPServer.
- [ ] Minimize lag between finish downloading and start processing.
- [ ] Direct link for downloading.
- [ ] Multi-process support.
- [ ] Security, logging, error catching, response to user.

