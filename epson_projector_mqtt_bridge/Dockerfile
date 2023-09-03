ARG BUILD_FROM
FROM $BUILD_FROM

#ARG S6_OVERLAY_VERSION=3.1.5.0


#ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
#RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz
#ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
#RUN tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-dev \
        git \
        build-essential \
    \
    && pip3 install --no-cache-dir -U setuptools wheel \
    && pip3 install --no-cache-dir -r ./requirements.txt \
    && rm -rf /var/lib/apt/lists/*

COPY rootfs /

ENTRYPOINT ["/init"]