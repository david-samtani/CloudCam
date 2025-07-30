# CloudCams

This is the project space for software and documentation related to the new CFHT cloud cameras.  


# How to build

```
docker build -t cloudcams:latest .
docker run -tid --name cloudcams-test cloudcams
docker exec -ti cloudcams-test "/bin/bash"
```