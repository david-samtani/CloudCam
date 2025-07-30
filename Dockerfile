FROM gitlab.cfht.hawaii.edu:5050/cfht/cfht-golden-image:latest

WORKDIR /opt/cloudcams

# install extra packages
# non-interactive
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y apt-utils python3 python-is-python3 pip && \
    apt-get clean

# copy in the source code
COPY astrometry-net-indexes/ astrometrynet_files/ data/ CloudCamOVR/CloudCamOVR250715/ data/ src/ temp_timeslapse .

# install needed python packages See requirements.txt.
RUN apt-get install -y python3-opencv python3-matplotlib python3-numpy python3-astropy python3-skyfield python3-photutils

#ENTRYPOINT ["python", "/opt/cloudcams/src/automated_process.py"]
# Used for testing
ENTRYPOINT ["sleep", "infinity"]
