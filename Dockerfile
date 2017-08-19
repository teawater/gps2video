# may use alpine to make it small
FROM dkarchmervue/python27-ffmpeg

ENV GPS2VIDEO_HOME /var/lib/gps2video
ENV PATH $PATH:$GPS2VIDEO_HOME

RUN pip install gpxpy Pillow

COPY . $GPS2VIDEO_HOME
