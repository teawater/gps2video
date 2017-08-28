gps2video是一个用来将GPS轨迹转化为视频的软件。
***
```
sudo pip install gpxpy urllib2 pillow
git clone https://github.com/teawater/gps2video.git
cd gps2video
python gps2video.py
```
然后按照输出做即可。
***
更新记录：
* 2017.08.28<br>
  增加命令行配置功能。<br>
  增加把轨迹点替换为头像图片的功能。详见配置文件选项head_file和head_size。
