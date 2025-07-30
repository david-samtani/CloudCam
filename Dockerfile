FROM gitlab.cfht.hawaii.edu:5050/cfht/cfht-golden-image:latest-dev

WORKDIR /opt/cloudcams

# install extra packages
# non-interactive
ARG DEBIAN_FRONTEND=noninteractive
ENV astrometry_version="0.97"
ENV astrometry_src="https://astrometry.net/downloads/astrometry.net-${astrometry_version}.tar.gz"

# Install Tools and Python packages
RUN apt-get update && \
    apt-get install -y apt-utils python3 python3-dev python-is-python3 xvfb pip wget \
            python3-opencv python3-tk python3-matplotlib python3-numpy python3-astropy python3-skyfield python3-photutils \
            libx11-dev libcairo2-dev libnetpbm10-dev netpbm libpng-dev libjpeg-dev zlib1g-dev libbz2-dev swig && \
    apt-get clean

# Note the LDAP uid/gin for mongodb
ARG CLOUDCAM_UID="759"
ARG CLOUDCAM_GID="759"

# Set UID/GID for oxidize
RUN groupadd -g ${CLOUDCAM_GID} cloudcam && \
    useradd -u ${CLOUDCAM_UID} -g ${CLOUDCAM_GID} -m -s /bin/bash cloudcam

# copy in the source code
RUN mkdir -p src astrometry-net-indexes astrometrynet_files data
COPY src/ ./src/
COPY astrometry-net-indexes/ ./astrometry-net-indexes/
COPY astrometrynet_files/ ./astrometrynet_files/
COPY data/ ./data

#Download astrometry source
RUN wget ${astrometry_src} && \
    tar -xzvf astrometry.net-${astrometry_version}.tar.gz

    # Copied modified C files into astrometry source
COPY ./plot/plot-constellations.c ./astrometry.net-${astrometry_version}/plot/
COPY ./solve/solve-field.c ./astrometry.net-${astrometry_version}/slove/

RUN cd astrometry.net-${astrometry_version} && \
    make install && \
    cd ..; ln -s astrometry.net-${astrometry_version} astrometry.net && \
    rm astrometry.net-0.97.tar.gz && \
    chown cloudcam:cloudcam /opt/cloudcams/ -R

USER cloudcam
    #ENTRYPOINT ["python", "/opt/cloudcams/src/automated_process.py"]
# Used for testing
ENTRYPOINT ["xvfb-run","-s","-screen 0 1280x720x24","sleep","infinity"]
