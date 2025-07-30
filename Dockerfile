FROM gitlab.cfht.hawaii.edu:5050/cfht/cfht-golden-image:latest-dev

WORKDIR /opt/cloudcams

# install extra packages
# non-interactive
ARG DEBIAN_FRONTEND=noninteractive
ARG HOST_UID=1000
ARG HOST_GID=1000
ENV astrometry_version="0.97"
ENV astrometry_src="https://astrometry.net/downloads/astrometry.net-${astrometry_version}.tar.gz"

# Install Tools and Python packages
RUN apt-get update && \
    apt-get install -y apt-utils python3 python3-dev python-is-python3 xvfb pip wget \
            python3-opencv python3-ffmpeg python3-tk python3-matplotlib python3-numpy python3-astropy python3-skyfield python3-photutils \
            libx11-dev libcairo2-dev libnetpbm10-dev netpbm libpng-dev libjpeg-dev zlib1g-dev libbz2-dev swig && \
    apt-get clean

# Install X11 libraries
RUN apt-get install -y \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-xfixes0 \
    libxcb-xinerama0 libxkbcommon-x11-0

# Note the LDAP uid/gin for mongodb
RUN groupadd  -g ${HOST_GID} cloudcam && \
    useradd   -u ${HOST_UID} -g ${HOST_GID} -m -s /bin/bash cloudcam

# copy in the source code
COPY ./src ./src
COPY ./astrometry-net-indexes ./astrometry-net-indexes
COPY ./astrometrynet_files ./astrometrynet_files
COPY ./data ./data


#Download astrometry source
ADD ${astrometry_src} ./
RUN wget ${astrometry_src} && \
    tar -xzvf astrometry.net-${astrometry_version}.tar.gz

    # Copied modified C files into astrometry source
COPY ./plot/plot-constellations.c ./astrometry.net-${astrometry_version}/plot/
COPY ./solve/solve-field.c ./astrometry.net-${astrometry_version}/solve/

RUN cd astrometry.net-${astrometry_version} && \
    make install && \
    cd ..; ln -s astrometry.net-${astrometry_version} astrometry.net && \
    rm astrometry.net-0.97.tar.gz && \
    chown cloudcam:cloudcam /opt/cloudcams/ -R

USER cloudcam
    #ENTRYPOINT ["python", "/opt/cloudcams/src/automated_process.py"]
# Used for testing
ENTRYPOINT ["python3", "/opt/cloudcams/src/automated_process.py"]
