FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=true

# Install Pillow dependencies (see https://pillow.readthedocs.io/en/stable/installation.html#building-from-source)
RUN apt-get update
RUN apt-get -y install git wget libtiff5-dev libjpeg62-turbo-dev libopenjp2-7-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python3-tk \
    libharfbuzz-dev libfribidi-dev libxcb1-dev

RUN mkdir -p /app/out
WORKDIR /app

# install CPU-only torch on linux to minimize index size
RUN if [ "`uname -m`" = "x86_64" ] ; then \
       echo "Installing CPU-only pytorch" ; \
       pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu ; \
    fi

RUN git clone https://github.com/ReolinkCameraAPI/reolinkapipy.git
COPY reolinkapipy-fixes.patch reolinkapipy
WORKDIR /app/reolinkapipy
RUN git apply reolinkapipy-fixes.patch
RUN pip install .
RUN pip install ".[streaming]"
WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

# pre-download model files
RUN wget -P models https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l.pt

COPY egg_detector /app/egg_detector
COPY tests /app/tests
COPY test_images /app/test_images

CMD ["python", "-m", "egg_detector.main"]

