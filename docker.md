# Introduction #
Here is the simple guideline on how to run inside docker environment

<pre>
# put sample.gpx/config.ini under current folder
# update filename and provide map api key
#
docker build -t gps2video .
docker run -it -v $PWD:/gpx -w /gpx gps2video gps2video.py
</pre>

# TODO #
- turn script to accept command line parameter
- fix bug to use /use/bin/python in the header
- `Dockerfile`
- May make service to deploy in http://hyper.sh 
