
FROM node:20-bookworm
ENV DEBIAN_FRONTEND=noninteractive ANDROID_HOME=/opt/android-sdk ANDROID_SDK_ROOT=/opt/android-sdk JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jdk-headless wget unzip zip python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN mkdir -p $ANDROID_HOME/cmdline-tools && wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/sdk.zip && unzip -q /tmp/sdk.zip -d $ANDROID_HOME/cmdline-tools && mv $ANDROID_HOME/cmdline-tools/cmdline-tools $ANDROID_HOME/cmdline-tools/latest && rm /tmp/sdk.zip
RUN yes | sdkmanager --licenses >/dev/null 2>&1 || true
RUN sdkmanager --install "platform-tools" "platforms;android-35" "build-tools;35.0.0"
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PORT=10000 DATA_DIR=/tmp/apk-server-data
EXPOSE 10000
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
