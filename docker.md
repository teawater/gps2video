# Introduction #
Here is the simple guideline on how to run inside docker environment

<pre>
# put sample.gpx under current folder
docker run -it -v $PWD:/gpx -w /gpx dkarchmervue/python27-ffmpeg bash
# git clone https://github.com/teawater/gps2video.git
# pip install gpxpy Pillow
## copy example.ini to config.ini
## update filename and provide map api key
# python gps2video.py
</pre>

# TODO #
- turn script to accept command line parameter
- fix bug to use /use/bin/python in the header
- `Dockerfile`
- May make service to deploy in http://hyper.sh 
