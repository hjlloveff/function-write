FROM python:2.7

COPY . /usr/src/app
# RUN pip install -i http://pypi-sh.emotibot.com:3141/deployer/dev --trusted-host=pypi-sh.emotibot.com -r /usr/src/app/requirements.txt
RUN pip install -r /usr/src/app/requirements.txt
RUN python -m compileall /usr/src/app 
RUN find /usr/src/app -type f -name '*.py' -exec rm {} \;

WORKDIR "/usr/src/app"
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
