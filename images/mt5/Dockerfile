FROM debian:bookworm-slim

ENV HOME /root
ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

RUN apt update && \
    apt-get -y install xvfb x11vnc xdotool wget tar supervisor net-tools fluxbox gnupg2 wine64 dh-python xterm && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ADD ./WORK/winepre.tgz /

COPY ./WORK/CODE /CODE

ENV WINEPREFIX /winepre
ENV WINEARCH win64
ENV WINEDLLOVERRIDES=mscoree=d 
ENV DISPLAY :0

WORKDIR /root/
RUN wget -O - https://github.com/novnc/noVNC/archive/v1.4.0.tar.gz | tar -xzv -C /root/ && mv /root/noVNC-1.4.0 /root/novnc && ln -s /root/novnc/vnc_lite.html /root/novnc/index.html && \
    wget -O - https://github.com/novnc/websockify/archive/v0.11.0.tar.gz | tar -xzv -C /root/ && mv /root/websockify-0.11.0 /root/novnc/utils/websockify

EXPOSE 8080

CMD ["/usr/bin/supervisord"]

