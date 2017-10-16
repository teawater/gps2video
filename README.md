gps2video是一个用来将GPS轨迹转化为视频的软件。
***
```
sudo apt-get install ffmpeg
sudo pip install gpxpy urllib2 pillow
git clone https://github.com/teawater/gps2video.git
cd gps2video
python gps2video.py --help
```
然后按照输出做即可。
***
更新记录：
* 2017.10.17<br>
  当选项video_limit_secs比较小而照片比较多的时候，自动跳过一定数量的照片。
* 2017.10.16<br>
  修正无法找到camera.png的错误。
* 2017.10.15<br>
  photos_timezone选项支持浮点数，因为有3.5这种时区。<br>
  支持从配置文件中取得照片的创建时间。
* 2017.09.02<br>
  增加自动限制视频时间长度的功能，再不用担心朋友圈发视频要截掉一段啦，详见配置文件选项video_limit_secs。
* 2017.09.01<br>
  增加视频解码器设置功能，并将默认值设置为libx264，详见配置文件选项video_codec。<br>
  增加自动复用上次地图的功能，详见配置文件选项map_cache。<br>
  增加设置结尾轨迹信息图显示秒数的功能，详见配置文件选项trackinfo_show_sec。
* 2017.08.31<br>
  增加在视频中添加照片的功能。详见配置文件选项photos_dir，photos_timezone和photos_show_secs。<br>
  把用来隐藏开头若干距离的轨迹的项目hide_head重命名为hide_begin。
* 2017.08.28<br>
  增加命令行配置功能。<br>
  增加把轨迹点替换为头像图片的功能。详见配置文件选项head_file和head_size。
