ARG BUILD_FROM
FROM $BUILD_FROM

WORKDIR /usr/src/app

COPY . .

RUN \
    set -x \
    && apk add --no-cache \
        py3-pip \
        python3 \
    && pip3 install --no-cache-dir -r requirements.txt

COPY rootfs /

ENTRYPOINT ["/init"]