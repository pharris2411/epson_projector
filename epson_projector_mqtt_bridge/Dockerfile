ARG BUILD_FROM
FROM $BUILD_FROM

#ARG S6_OVERLAY_VERSION=3.1.5.0

## Install requirements for add-on
RUN \
    set -x \
    && apk add --no-cache \
        py3-pip \
        python3 \

#ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
#RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz
#ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
#RUN tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY rootfs /

ENTRYPOINT ["/init"]