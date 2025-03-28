FROM amazon/aws-lambda-python:3.12

# install chrome dependencies
RUN dnf install -y atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm jq unzip

COPY ./chrome-installer.sh ./chrome-installer.sh
RUN ./chrome-installer.sh
RUN rm ./chrome-installer.sh


# Set working directory
WORKDIR /var/task

# Install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}


RUN pip install -r requirements.txt

# # Copy Lambda function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}


# # Set the Lambda handler
CMD ["lambda_function.handler"]


