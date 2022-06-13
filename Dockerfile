FROM ubuntu:bionic

RUN apt-get update && apt-get install python3 python3-pip curl unzip -yf

# Install Chrome
RUN apt-get update -y
RUN curl https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o /chrome.deb
RUN dpkg -i /chrome.deb || apt-get install -yf
RUN rm /chrome.deb
RUN apt-get update -y
RUN apt-get -y install libssl1.0-dev
# May be not correct version of driver...
RUN curl https://chromedriver.storage.googleapis.com/102.0.5005.61/chromedriver_linux64.zip -o /usr/local/bin/chromedriver.zip
RUN cd /usr/local/bin && unzip chromedriver.zip
RUN chmod +x /usr/local/bin/chromedriver
USER root
RUN apt update
RUN apt-get clean
RUN apt install -y python3 python3-pip
RUN pip3 install virtualenv
RUN mkdir /app
RUN mkdir /app/screenshots
COPY requirements.txt /app
WORKDIR /app
RUN virtualenv .venv
RUN /bin/bash -c "source .venv/bin/activate"
RUN pip3 install --no-cache-dir -r requirements.txt
# RU language can be turned off for ENG
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y language-pack-ru
ENV LANGUAGE ru_RU.UTF-8
ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8
RUN locale-gen ru_RU.UTF-8 && dpkg-reconfigure locales

# TZ
RUN apt-get install -y tzdata=2018d-1
RUN ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN dpkg-reconfigure -f noninteractive tzdata
COPY . /app
ENTRYPOINT [ "python3", "WA_cloud_bot.py" ]